# package imports
import asyncio
import time
from confluent_kafka.admin import AdminClient
from confluent_kafka import Producer, Consumer
from confluent_kafka.error import KafkaException, KafkaError
import socket
import sys


# Asynchronous writes
def produce_acked(err, msg):
    '''Callback function for producing messages to the server'''
    if err is not None:
        print('Failed to deliver message: %s: %s' % (str(msg), str(err)))
    else:
        print('Message produced: %s' % (str(msg)))


# Consume loop
def consume_key_value(consumer, topics):
    '''
    Simple consume loop that will keep the latest value
    There might be a better way to write this
    '''
    running = True
    val = None
    try:
        consumer.subscribe(topics)

        while running:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                running = False
                continue

            if msg.error():
                print('msg error')
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # End of partition event
                    sys.stderr.write('%% %s [%d] reached end at offset %d\n' %
                                     (msg.topic(), msg.partition(), msg.offset()))
                elif msg.error():
                    raise KafkaException(msg.error())
            else:
                val = msg.value()
    finally:
        # Close down consumer
        consumer.close()
        return val


DEFAULT_KAFKA_SERVERS = ['localhost:9092']

class KafkaKVS:
    '''
    Implement a KVS based on Kafka log compaction
    '''
    def __init__(self, bootstrap_servers=DEFAULT_KAFKA_SERVERS):
        '''
        Create a new KafkaKVS.
        `bootstrap_servers` is a list of Kafka servers.
        '''
        # initialize self variables
        self.bootstrap_servers = ','.join(bootstrap_servers) # servers are passed as a string separated by commas

        # initialize admin client
        config = {
            'bootstrap.servers': self.bootstrap_servers
        }
        self.admin_client = AdminClient(config)

        # initialize producer
        config = {
            'bootstrap.servers': self.bootstrap_servers,
            'client.id': socket.gethostname()
        }
        self.producer = Producer(config)


    async def __getitem__(self, key):
        '''
        Syntax:

        >> await kvs['item']
        '''

        # initialize consumer
        config = {
            'bootstrap.servers': self.bootstrap_servers,
            'group.id': 'foo',
            'enable.auto.commit': False,
            'auto.offset.reset': 'earliest'
        }
        consumer = Consumer(config)
        value = consume_key_value(consumer, [key])
        return value

    async def set(self, key, value):
        '''
        Syntax:
        >> await set('key', value)

        `key` is a string, and `value` is a json object.

        We can't use a setter with async, as far as I can tell. There is no

        `await kvs['item'] = foo

        So we use an explict set function.
        '''
        # if auto topic creation is disabled on the server, then
        # we need to make sure the topic exists before producing a value to it.
        self.producer.produce(key, value=value, callback=produce_acked)
        self.producer.poll(1)

    async def keys(self):
        '''
        Returns all keys.

        Currently this filters out any internal topics, anything that starts with _

        Eventually, this might support wildcards.
        '''
        all_topics = self.admin_client.list_topics().topics
        topics = [t for t in all_topics if not t.startswith('_')]  # filter out internal topics
        return topics

    async def clear(self):
        '''
        Clear the KVS.

        This is helpful for debugging and testing. We did not want to
        implement this for the production KVS, since it would be
        too easy to accidentally lose data.
        '''
        # Should we keep a running list of Keys in the class
        pass


async def test():
    '''
    Simple testing method
    '''
    kvs = KafkaKVS()
    await kvs.set('brad', 'first_value')
    time.sleep(2)
    await kvs.set('brad', 'second_value')
    time.sleep(2)
    await kvs.set('collin', 'first_value')
    time.sleep(2)
    await kvs.set('collin', 'second_value')
    time.sleep(2)
    await kvs.set('collin', 'third_value')
    time.sleep(2)
    kvs.producer.flush()

    collin = await kvs['collin']
    brad = await kvs['brad']

    print(f'Collin: {collin}')
    print(f'Brad: {brad}')

    await kvs.set('collin', 'next_value')
    collin = await kvs['collin']
    print(f'Collin2: {collin}')

    topics = await kvs.keys()
    print(f'Total topics: {len(topics)}')


if __name__ == '__main__':
    asyncio.run(test())
