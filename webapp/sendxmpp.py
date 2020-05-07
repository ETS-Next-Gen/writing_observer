from slixmpp import ClientXMPP
from slixmpp.exceptions import IqError, IqTimeout

class SendXMPP(ClientXMPP):
    def __init__(self, jid, password, debug_log):
        self.debug_log = debug_log
        ClientXMPP.__init__(self, jid, password)
        self.add_event_handler("session_start", self.session_start)
        self.add_event_handler("message", self.message)

    def session_start(self, event):
        self.send_presence()
        self.get_roster()
        self.debug_log("XMPP sender session initialized")

    def message(self, msg):
        pass
        #print("Unexpected! I shouldn't get messages")

    def send_event(self, mto, mbody):
        self.send_message(
            mto=mto,
            mbody=mbody,
            mtype='chat')
        self.debug_log("XMPP message sent")
