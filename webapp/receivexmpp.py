import asyncio

from lxml import etree

from slixmpp import ClientXMPP
from slixmpp.exceptions import IqError, IqTimeout

class ReceiveXMPP(ClientXMPP):
    def __init__(self, jid, password, callback=lambda x:None):
        ClientXMPP.__init__(self, jid, password)
        self.callback = callback
        self.add_event_handler("session_start", self.session_start)
        self.add_event_handler("message", self.message)
        self.msg_future = self.new_future()

    def new_future(self):
        return asyncio.get_event_loop().create_future()

    def session_start(self, event):
        self.send_presence()
        self.get_roster()

    async def receive(self):
        await self.msg_future
        rv = self.msg_future.result()
        self.msg_future=self.new_future()
        xml_tree = etree.fromstring(rv)
        payload = etree.tostring(xml_tree, encoding='utf8', method='text').decode('utf8')
        return(payload)

    async def message(self, msg):
        #print("XMPP Received"+str(msg))
        #print(msg)
        self.msg_future.set_result(str(msg))
        #if msg['type'] in ('chat', 'normal'):
        #    msg.reply("Thanks for sending\n%(body)s" % msg).send()
