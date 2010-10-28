"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

import logging
import threading

from sleekxmpp.xmlstream.handler.callback import Callback
from sleekxmpp.xmlstream.matcher.xmlmask import MatchXMLMask

from sleekbot.plugbot import BotPlugin

MASK = "<message xmlns='jabber:client' type='error'>"  \
       "<error type='modify' code='406' >" \
       "<not-acceptable xmlns='urn:ietf:params:xml:ns:xmpp-stanzas'/>"  \
       "</error></message>"


class MUCStability(BotPlugin):
    """ Attempts to keep Sleek in muc channels."""

    def __init__(self, *args, **kwargs):
        super(MUCStability, self).__init__(*args, **kwargs)
        self.__event = threading.Event()

    def _on_register(self):
        """ Register stanza and corresponding handler."""
        callback = Callback("groupchat_error", MatchXMLMask(MASK), 
                            self.handle_message_error)
        self.bot.registerHandler(callback)                
        threading.Thread(target=self.loop).start()

    def _on_unregister(self):
        self.__event.set()
                          
    def loop(self):
        """ Send message to MUCs."""
        while not self.__event.is_set():
            if self.bot.plugin['xep_0045']:
                for muc in self.bot.plugin['xep_0045'].getJoinedRooms():
                    jid = self.bot.plugin['xep_0045'].getOurJidInRoom(muc)
                    self.bot.send_message(jid, None, mtype='chat')
            self.__event.wait(540)

    def handle_message_error(self, msg):
        """ On error messages, see if it's from a muc, and rejoin the muc if so.
            (Subtle as a flying mallet)
        """
        room = msg['from'].bare
        if room not in self.bot.plugin['xep_0045'].getJoinedRooms():
            return
        nick = self.bot.plugin['xep_0045'].ourNicks[room]
        logging.debug("muc_stability: error from %s, rejoining as %s", 
                      room, nick)
        self.bot.plugin['xep_0045'].joinMUC(room, nick)
