"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

import datetime
import time
import logging

from sleekbot.commandbot import botcmd
from sleekbot.plugbot import BotPlugin

class seenevent(object):
    """ Represent the last know activity of a user.
    """
    messageType = 0
    joinType = 1
    partType = 2
    presenceType = 3

    def __init__(self, nick, eventTime, muc, stanzaType, text=None):
        """ Initialise seenevent
        """
        self.nick = nick
        self.eventTime = eventTime
        self.muc = muc
        self.stanzaType = stanzaType
        self.text = text

class jidevent(object):
    """ Represent the last seen jid of a user.
    """
    def __init__(self, muc, nick, jid, eventTime):
        """Create event"""
        self.muc = muc
        self.nick = nick
        self.jid = jid
        self.eventTime = eventTime

class jidstore(object):
    def __init__(self, store):
        self.store = store
        self.createTable()

    def createTable(self):
        db = self.store.getDb()
        if not len(db.execute("pragma table_info('whowas')").fetchall()) > 0:
            db.execute("""CREATE TABLE whowas (
                       id INTEGER PRIMARY KEY AUTOINCREMENT, muc VARCHAR(256),
                       nick VARCHAR(256), jid VARCHAR(256), eventTime DATETIME)""")
        db.close()

    def update(self, event):
        db = self.store.getDb()
        cur = db.cursor()
        logging.debug("Updating whowas")
        cur.execute('SELECT * FROM whowas WHERE nick=? AND muc=?', (event.nick,event.muc))
        if (len(cur.fetchall()) > 0):
            cur.execute('UPDATE whowas SET jid=?, eventTime=?', (event.jid, event.eventTime))
            logging.debug("Updated existing whowas")
        else:
            cur.execute('INSERT INTO whowas(nick, muc, jid, eventTime) VALUES(?,?,?,?)',(event.nick, event.muc, event.jid, event.eventTime))
            logging.debug("Added new whowas")
        db.commit()
        db.close()


    def get(self, nick, muc):
        db = self.store.getDb()
        cur = db.cursor()
        cur.execute('SELECT * FROM seen WHERE nick=? AND muc=?', (nick,muc))
        results = cur.fetchall()
        if len(results) == 0:
            return None
        return jidevent(results[0][1],results[0][2],results[0][3],datetime.datetime.strptime(results[0][4][0:19],"""%Y-%m-%d %H:%M:%S""" ))
        db.close()

    def delete(self, nick, muc):
        db = self.store.getDb()
        cur = db.cursor()
        cur.execute('DELETE FROM seen WHERE nick=? AND muc=?', (nick,muc))
        db.commit()
        db.close()

class seenstore(object):
    def __init__(self, store):
        #self.null = None
        #self.data = {}
        #self.loaddefault()
        self.store = store
        self.createTable()

    def createTable(self):
        db = self.store.getDb()
        #Yes, I know this is completely denormalised, and if it becomes more complex I'll refactor the schema
        if not len(db.execute("pragma table_info('seen')").fetchall()) > 0:
            db.execute("""CREATE TABLE seen (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       nick VARCHAR(256), eventTime DATETIME, muc VARCHAR(256), stanzaType INTEGER, text VARCHAR(256))""")
        #if len(db.execute("pragma table_info('seen')").fetchall()) == 6:
        #    db.execute("""ALTER TABLE seen ADD COLUMN fullJid VARCHAR(256)""")
        db.close()

    def update(self, event):
        db = self.store.getDb()
        cur = db.cursor()
        logging.debug("Updating seen")
        cur.execute('SELECT * FROM seen WHERE nick=?', (event.nick,))
        if (len(cur.fetchall()) > 0):
            cur.execute('UPDATE seen SET nick=?, eventTime=?, muc=?, stanzaType=?, text=? WHERE nick=?', (event.nick, event.eventTime, event.muc, event.stanzaType, event.text, event.nick))
            logging.debug("Updated existing seen")
        else:
            cur.execute('INSERT INTO seen(nick, eventTime, muc, stanzaType, text) VALUES(?,?,?,?,?)',(event.nick, event.eventTime, event.muc, event.stanzaType, event.text))
            logging.debug("Added new seen")
        db.commit()
        db.close()


    def get(self, nick):
        db = self.store.getDb()
        cur = db.cursor()
        cur.execute('SELECT * FROM seen WHERE nick=?', (nick,))
        results = cur.fetchall()
        if len(results) == 0:
            return None
        return seenevent(results[0][1],datetime.datetime.strptime(results[0][2][0:19],"""%Y-%m-%d %H:%M:%S""" ),results[0][3],results[0][4],results[0][5])
        db.close()

    def delete(self, nick):
        db = self.store.getDb()
        cur = db.cursor()
        cur.execute('DELETE FROM seen WHERE nick=?', (nick,))
        db.commit()
        db.close()

class seen(BotPlugin):
    """A plugin to keep track of user presence."""

    def on_register(self):
        #BotPlugin.__init__(self, bot, config)
        self.seenstore = seenstore(self.bot.store)
        #self.bot.addIMCommand('whowas', self.handle_whowas_request)
        #self.bot.addMUCCommand('whowas', self.handle_whowas_request)
        #self.bot.addHelp('whowas', 'Jid of member', "See the last jid of a member", 'whowas')
        self.started = datetime.timedelta(seconds = time.time())
        self.bot.add_event_handler("groupchat_presence", self.handle_groupchat_presence, threaded=True)
        self.bot.add_event_handler("groupchat_message", self.handle_groupchat_message, threaded=True)

    def handle_groupchat_presence(self, presence):
        """ Keep track of the presences in mucs.
        """
        presence['dateTime'] = datetime.datetime.now()
        if presence.get('type', None) == 'unavailable':
            pType = seenevent.partType
        else:
            pType = seenevent.presenceType
        self.seenstore.update(seenevent(presence['nick'], presence['dateTime'], presence['room'], pType, presence.get('status', None)))
        #self.jidstore.update(jidevent(presence['nick'], presence['room'], self.bot.getRealJid(presence['jid']) , presence['dateTime']))



    def handle_groupchat_message(self, message):
        """ Keep track of activity through messages.
        """
        if 'message' not in message.keys():
            return
        message['dateTime'] = datetime.datetime.now()
        self.seenstore.update(seenevent(message['name'], message['dateTime'], message['room'], seenevent.messageType, message['message']))
        #self.jidstore.update(jidevent(message['name'], message['room'], self.bot.getRealJidFromMessag(message), message['dateTime']))

    @botcmd('seen')
    def handle_seen_request(self, command, args, msg):
        """See when a user was last seen."""
        if args == None or args == "":
            return "Please supply a a nickname to search for"
        seenData = self.seenstore.get(args)
        if seenData == None:
            return "I have never seen '" + args + "'"
        sinceTimeSeconds = (datetime.datetime.now() - seenData.eventTime).seconds
        sinceTime = ""
        if sinceTimeSeconds >= 3600:
            sinceTime = "%d hours ago" % (sinceTimeSeconds / 3600)
        elif sinceTimeSeconds >= 60:
            sinceTime = "%d minutes ago" % (sinceTimeSeconds / 60)
        else:
            sinceTime = "%d seconds ago" % sinceTimeSeconds
        status = ""
        if seenData.stanzaType == seenevent.messageType:
            status = "saying '%s'" % seenData.text
        elif seenData.stanzaType == seenevent.presenceType and seenData.text is not None:
            status = "(%s)" % seenData.text
        state = "in"
        if seenData.stanzaType == seenevent.partType:
            state = "leaving"
        #if seenData['show'] == None:
        #    state = "joining"
        return "'%s' was last seen %s %s %s %s"  %(args, state, seenData.muc, sinceTime, status)
