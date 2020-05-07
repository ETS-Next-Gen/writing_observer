import asyncio

from lxml import etree

from slixmpp import ClientXMPP
from slixmpp.exceptions import IqError, IqTimeout

class Message(str):
    '''
    This is a string-like object width additional attributes for:
    * `message_type` (e.g. 'chat')
    * `message_to` -- the destination
    * `message_from` -- the source
    * `message_id` -- conveniently added by prosody (and hopefully
      other servers)

    This lets us operate relatively seamlessly with non-XMPP code and
    preserve (some) abstraction.
    '''
    def __new__(cls, msg):
        xml_tree = etree.fromstring(msg)
        s = super().__new__(cls, etree.tostring(xml_tree, encoding='utf8', method='text').decode('utf8'))

        # We do this explicitly to sanitize inputs
        # (Although this is coming from a (relatively) secure source)
        s.message_type = xml_tree.attrib['type']
        s.message_to = xml_tree.attrib['to']
        s.message_id = xml_tree.attrib['id']
        s.message_from = xml_tree.attrib['from']

        return s

class ReceiveXMPP(ClientXMPP):
    def __init__(self, jid, password, debug_log=lambda x:None):
        self.debug_log = debug_log
        ClientXMPP.__init__(self, jid, password)
        self.add_event_handler("session_start", self.session_start)
        self.add_event_handler("message", self.message)
        self.msg_future = self.new_future()

    def new_future(self):
        return asyncio.get_event_loop().create_future()

    def session_start(self, event):
        self.send_presence()
        self.get_roster()
        self.debug_log("XMPP receiver started")

    async def receive(self):
        self.debug_log("Waiting for XMPP message")
        await self.msg_future
        rv = self.msg_future.result()
        self.msg_future=self.new_future()
        return Message(rv)

    async def message(self, msg):
        self.debug_log("XMPP message received")
        self.msg_future.set_result(str(msg))
        # For debugging, we sometimes want to send something back
        if msg['type'] in ('chat', 'normal'):
            msg.reply("Thanks for sending\n%(body)s" % msg).send()
