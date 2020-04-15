from slixmpp import ClientXMPP
from slixmpp.exceptions import IqError, IqTimeout

class ReceiveXMPP(ClientXMPP):
    def __init__(self, jid, password, callback=lambda x:None):
        ClientXMPP.__init__(self, jid, password)
        self.callback = callback
        self.add_event_handler("session_start", self.session_start)
        self.add_event_handler("message", self.message)

    def session_start(self, event):
        self.send_presence()
        self.get_roster()

    def message(self, msg):
        print("Received")
        print(msg);
        self.callback(msg)
        if msg['type'] in ('chat', 'normal'):
            msg.reply("Thanks for sending\n%(body)s" % msg).send()
