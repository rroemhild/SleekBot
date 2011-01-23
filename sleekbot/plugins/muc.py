"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""


import logging
import threading

from sleekbot.commandbot import botcmd, CommandBot, denymsg
from sleekbot.commandbot import parse_args, ArgError

from sleekxmpp.xmlstream.handler.callback import Callback
from sleekxmpp.xmlstream.matcher.xmlmask import MatchXMLMask

from sleekbot.plugbot import BotPlugin


class MUC(BotPlugin):
    """ Plugin to manage Multi User Chats."""

    def _on_register(self):
        self.muc = self.bot.plugin['xep_0045']
        self.nick = self.config.find('rooms').get('default_nick', 'SleekBot')
        self.bot.add_event_handler("session_start", self.handle_session_start, 
                                   disposable=True)

    def handle_session_start(self, event):
        """ Join MUC rooms when session is established.
        """
        logging.info("Joining MUC rooms")
        xrooms = self.config.findall('rooms/muc')
        rooms = {}
        for xroom in xrooms:
            rooms[xroom.attrib['room']] = xroom.attrib['nick']
        self.join_room(rooms)

    def join_room(self, rooms):
        """ Join one or more rooms.
        """
        for room in set(rooms.keys()).difference(self.bot.rooms.keys()):
            self.bot.rooms[room] = rooms[room]
            logging.info("Joining room %s as %s." % (room, rooms[room]))
            self.muc.joinMUC(room, rooms[room])        

    @botcmd(usage="[roomname] [join | leave | kick | ban | kickban | " \
                    "invite | set | show | topic | rooms | nick | priv | " \
                    "users | startup] [<option>]",
                    allow=CommandBot.msg_from_admin)
    def muc(self, command, args, msg):
        """ Manage a Multi-User-Chat.
        """
        try:
            args = parse_args(args, (('action', (str, 'join', 'leave', 'invite',
                                    'topic', 'rooms', )), ('room', ''), ))
        except ArgError as error:
            return error.msg

        args.parsed_ = False
        return getattr(self, 'muc_' + args.action,)(command, args, msg)

    @botcmd(usage='roomname <nick>', allow=CommandBot.msg_from_admin, hidden=True)
    def muc_join(self, command, args, msg):
        """ Join a Multi-User-Chat room.
        """
        
        try:
            args = parse_args(args, (('action', (str, 'join')),
                                    ('room', str), ('nick', self.nick), ))
        except ArgError as error:
            return error.msg
        
        self.join_room({args.room: args.nick})

    @botcmd(usage='roomname', allow=CommandBot.msg_from_admin, hidden=True)
    def muc_leave(self, command, args, msg):
        """ Leave a Multi-User-Chat room.
        """

        try:
            args = parse_args(args, (('action', (str, 'leave')),
                                    ('room', str), ('msg', ''), ))
        except ArgError as error:
            return error.msg

        logging.info("Leaving MUC room %s as %s.", args.room,
                                                   self.bot.rooms[args.room])
        self.muc.leaveMUC(args.room, self.bot.rooms[args.room], args.msg)
        del self.bot.rooms[args.room]

    @botcmd(usage='nick <roomname> <reason>', allow=CommandBot.msg_from_admin,
        hidden=True)
    def muc_invite(self, command, args, msg):
        """ Invite a victim to join a room.
        """
        
        try:
            args = parse_args(args, (('action', (str, 'invite')),
                                    ('jid', str), ('room', ''),
                                    ('reason', ''), ))
        except ArgError as error:
            return error.msg
        
        if not args.room:
            croom = msg['mucroom']
        else:
            croom = args.room
        
        self.muc.invite(croom, args.jid, args.reason)
        logging.info("Invited %s to %s.", args.jid, croom)

    @botcmd(allow=CommandBot.msg_from_admin, hidden=True)
    def muc_rooms(self, command, args, msg):
        """ Return Room names the bot has joined.
        """
        return "Rooms I joined: %s" % self.bot.rooms.keys()

    @botcmd(usage="topic <roomname>", allow=CommandBot.msg_from_admin,
            hidden=True)
    def muc_topic(self, command, args, msg):
        """ Set a rooms topic
        """
        
        try:
            args = parse_args(args, (('action', (str, 'topic')),
                                     ('room', ''), ))
        except ArgError as error:
            return error




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
        """ On error messages, see if it's from a muc, and rejoin the muc if
            so. (Subtle as a flying mallet)
        """
        room = msg['from'].bare
        if room not in self.bot.plugin['xep_0045'].getJoinedRooms():
            return
        nick = self.bot.plugin['xep_0045'].ourNicks[room]
        logging.debug("muc_stability: error from %s, rejoining as %s", 
                      room, nick)
        self.bot.plugin['xep_0045'].joinMUC(room, nick)

