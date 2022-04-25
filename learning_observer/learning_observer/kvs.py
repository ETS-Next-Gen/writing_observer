'''Key-
value store

Manages JSON objects

kvs.KVS() will return a key-value store. Note that the back-end is
shared, but each

Keys are strings. Values are JSON objects.

To read objects:

'''

import asyncio
import copy
import json
import sys

import asyncio_redis

import learning_observer.prestartup
import learning_observer.settings
import learning_observer.redis

OBJECT_STORE = dict()


class InMemoryKVS():
    '''
    Stores items in-memory. Items expire on system restart.
    '''
    async def __getitem__(self, key):
        '''
        Syntax:

        >> await kvs['item']
        '''
        return copy.deepcopy(OBJECT_STORE.get(key, None))

    async def set(self, key, value):
        '''
        Syntax:
        >> await set('key', value)

        `key` is a string, and `value` is a json object.

        We can't use a setter with async, as far as I can tell. There is no

        `await kvs['item'] = foo

        So we use an explict set function.
        '''
        json.dumps(value)  # Fail early if we're not JSON
        assert isinstance(key, str), "KVS keys must be strings"
        OBJECT_STORE[key] = value

    async def keys(self):
        '''
        Returns all keys.

        Eventually, this might support wildcards.
        '''
        return list(OBJECT_STORE.keys())


class _RedisKVS():
    '''
    Stores items in redis.
    '''
    def __init__(self, expire):
        self.expire = expire

    async def connect(self):
        '''
        asyncio_redis auto-reconnects. We can't do async in __init__. So
        we connect on the first get / set.
        '''
        await learning_observer.redis.connect()

    async def __getitem__(self, key):
        '''
        Syntax:

        >> await kvs['item']
        '''
        await self.connect()
        connection = await learning_observer.redis.connection()
        item = await connection.get(key)
        if item is not None:
            return json.loads(item)
        return None

    async def set(self, key, value):
        '''
        Syntax:
        >> await set('key', value)

        `key` is a string, and `value` is a json object.

        We can't use a setter with async, as far as I can tell. There is no

        `await kvs['item'] = foo

        So we use an explict set function.
        '''
        await self.connect()
        json.dumps(value)  # Fail early if we're not JSON
        assert isinstance(key, str), "KVS keys must be strings"
        connection = await learning_observer.redis.connection()
        await connection.set(key, json.dumps(value), expire=self.expire)
        return

    async def keys(self):
        '''
        Return all the keys in the KVS.

        This is obviously not very performant for large-scale dpeloys.
        '''
        await self.connect()
        connection = await learning_observer.redis.connection()
        return [await k for k in await connection.keys("*")]


class EphemeralRedisKVS(_RedisKVS):
    '''
    For testing: redis drops data quickly.
    '''
    def __init__(self):
        '''
        We're just a `_RedisKVS` with expiration set
        '''
        super().__init__(expire=learning_observer.settings.settings['kvs']['expiry'])


class PersistentRedisKVS(_RedisKVS):
    '''

    For deployment: Data lives forever.
    '''
    def __init__(self):
        '''
        We're just a `_RedisKVS` with expiration unset
        '''
        super().__init__(expire=None)


@learning_observer.prestartup.register_startup_check
def kvs_startup_check():
    '''
    This is a startup check. If confirms that the KVS is properly configured
    in settings.py. It should happen after we've loaded settings.py, so we
    register this to run in prestartup.

    Checks like this one allow us to fail on startup, rather than later
    '''
    try:
        KVS_MAP = {
            'stub': InMemoryKVS,
            'redis-ephemeral': EphemeralRedisKVS,
            'redis': PersistentRedisKVS
        }
        KVS = KVS_MAP[learning_observer.settings.settings['kvs']['type']]
    except KeyError:
        if 'kvs' not in learning_observer.settings.settings:
            raise learning_observer.prestartup.StartupCheck(
                "No KVS configured. Please set kvs.type in settings.py\n" \
                "Look at example settings file to see what's available."
            )
        elif learning_observer.settings.settings['kvs']['type'] not in KVS_MAP:
            raise learning_observer.prestartup.StartupCheck(
                "Unknown KVS type: {}\n" \
                "Look at example settings file to see what's available. \n"
                "Suppported types: {}".format(
                    learning_observer.settings.settings['kvs']['type'],
                    list(KVS_MAP.keys())
                )
            )
        else:
            raise learning_observer.prestartup.StartupCheck(
                "KVS incorrectly configured. Please fix the error, and\n" \
                "then replace this with a more meaningful error message"
            )
    return True


async def test():
    '''
    Simple test case: Spin up a few KVSes, write data to them, make
    sure it's persisted globally.
    '''
    mk1 = InMemoryKVS()
    mk2 = InMemoryKVS()
    ek1 = EphemeralRedisKVS()
    ek2 = EphemeralRedisKVS()
    assert(await mk1["hi"]) is None
    print(await ek1["hi"])
    assert(await ek1["hi"]) is None
    await mk1.set("hi", 5)
    await mk2.set("hi", 7)
    await ek1.set("hi", 8)
    await ek2.set("hi", 9)
    assert(await mk1["hi"]) == 7
    print(await ek1["hi"])
    print(type(await ek1["hi"]))
    print((await ek1["hi"]) == 9)
    assert(await ek1["hi"]) == 9
    print(await mk1.keys())
    print(await ek1.keys())
    print("Test successful")
    print("Please wait before running test again")
    print("redis needs to flush expiring objects")
    print("This delay is set in the config file.")
    print("It is typically 1s - 24h, depending on")
    print("the work.")

if __name__ == '__main__':
    asyncio.run(test())
