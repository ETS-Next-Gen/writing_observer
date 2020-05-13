'''
XMPP sender. This should probably be folded into receivexmpp, and
renamed xmpp_pubsub.

xmpp has a proper pubsub protocol, which me might also consider using
:)
'''

from slixmpp import ClientXMPP
from slixmpp.exceptions import IqError, IqTimeout


class SendXMPP(ClientXMPP):
    '''
    Gelper cla
    '''
    def __init__(self, jid, password, debug_log, mto):
        self.debug_log = debug_log
        self.mto = mto
        ClientXMPP.__init__(self, jid, password)
        self.add_event_handler("session_start", self.session_start)
        self.add_event_handler("message", self.message)

    def session_start(self, event):
        self.send_presence()
        self.get_roster()
        self.debug_log("XMPP sender session initialized")

    def message(self, msg):
        '''
        Callback for when a message is received. In theory, we thought
        this should never happen. In practice, we do get pings/acks of
        some kind, so we'll need to sort this out, and log an error
        for _unexpected_ messages.
        '''
        # print("Unexpected! I shouldn't get messages")
        pass

    async def send_event(self, mbody):
        self.send_message(
            mto=self.mto,
            mbody=mbody,
            mtype='chat')
        self.debug_log("XMPP message sent")
