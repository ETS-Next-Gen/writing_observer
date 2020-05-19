'''
We have several models for pub-sub:

1) We can use xmpp, which can run over prosody or eJabberd. These are
wickedly scaleable. We're not necessarily finished (as of the time of
this writing), which is to say they kind of work, but we sometimes
lose messages, and we can't direct them the right places.

2) We have a stubbed-in version. This only supports one user. It's
helpful for development and demos.

3) We're going to play with redis, which seems easier (but less scalable)
than xmpp, but is probably right approach for pilots.

One project which came up which might be relevant:
https://github.com/encode/broadcaster
'''

import settings

PUBSUB = settings.settings['pubsub']['type']

if PUBSUB == 'xmpp':
    import pubsub.receivexmpp
    import pubsub.sendxmpp

    async def pubsub_send(channel=None):
        sender = sendxmpp.SendXMPP(
            settings.SETTINGS['xmpp']['source']['jid'],
            settings.SETTINGS['xmpp']['source']['password'],
            debug_log,
            mto='sink@localhost'
        )
        sender.connect()
        return sender

    async def pubsub_receive(channel=None):
        receiver = receivexmpp.ReceiveXMPP(
            settings.SETTINGS['xmpp']['sink']['jid'],
            settings.SETTINGS['xmpp']['sink']['password'],
            debug_log
        )
        receiver.connect()
        return receiver
elif PUBSUB == 'stub':
    import pubsub.pubstub

    async def pubsub_send(channel=None):
        sender = pubstub.SendStub()
        return sender

    async def pubsub_receive(channel=None):
        receiver = pubstub.ReceiveStub()
        return receiver
elif PUBSUB == 'redis':
    import pubsub.redis_pubsub

    async def pubsub_send(channel=None):
        sender = redis_pubsub.RedisSend()
        await sender.connect()
        return sender

    async def pubsub_receive(channel=None):
        receiver = redis_pubsub.RedisReceive()
        await receiver.connect()
        return receiver
else:
    raise Exception("Unknown pubsub: "+PUBSUB)
