"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

import datetime
import time
import logging

from sleekbot.commandbot import botcmd
from sleekbot.plugbot import BotPlugin


class SeenEvent(object):
    """ Represent the last know activity of a user.
    """
    message_type = 0
    join_type = 1
    part_type = 2
    presence_type = 3

    def __init__(self, nick, event_time, muc, stanza_type, text=None):
        """ Initialise seenevent
        """
        self.nick = nick
        self.event_time = event_time
        self.muc = muc
        self.stanza_type = stanza_type
        self.text = text


class SeenStore(object):
    def __init__(self, store):
        self.store = store
        self.create_table()

    def create_table(self):
        """ Create the seen table."""

        with self.store.context_cursor() as cur:
            if not self.store.has_table(cur,'seen'):
                cur.execute("""CREATE TABLE seen (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            nick VARCHAR(256), eventTime DATETIME,
                            muc VARCHAR(256), stanzaType INTEGER,
                            text VARCHAR(256))""")

    def update(self, event):
        """ Update or insert a seen event."""

        with self.store.context_cursor() as cur:
            logging.debug("Updating seen for %s - time: %s", event.nick,
                                                            event.event_time)
            cur.execute('SELECT * FROM seen WHERE nick=?', (event.nick,))
            if (len(cur.fetchall()) > 0):
                cur.execute('UPDATE seen SET nick=?, eventTime=?, muc=?, ' +
                            'stanzaType=?, text=? WHERE nick=?', (event.nick,
                                                    event.event_time, event.muc,
                                                    event.stanza_type,
                                                    event.text, event.nick))
                logging.debug("Updated existing seen")
            else:
                cur.execute('INSERT INTO ' +
                            'seen(nick, eventTime, muc, stanzaType, text) ' +
                            'VALUES(?,?,?,?,?)', (event.nick, event.event_time,
                                                  event.muc, event.stanza_type,
                                                  event.text))
                logging.debug("Added new seen")

    def get(self, nick):
        """ Get a seen event."""

        with self.store.context_cursor() as cur:
            cur.execute('SELECT * FROM seen WHERE nick=?', (nick, ))
            results = cur.fetchall()
            if len(results) == 0:
                return None
            return SeenEvent(results[0][1], datetime.datetime.strptime(
                                                results[0][2][0:19],
                                                """%Y-%m-%d %H:%M:%S"""),
                                results[0][3], results[0][4], results[0][5])

    def delete(self, nick):
        """ Delete a seen event."""

        with self.store.context_cursor() as cur:
            cur.execute('DELETE FROM seen WHERE nick=?', (nick, ))


class Seen(BotPlugin):
    """A plugin to keep track of user presence."""

    def _on_register(self):
        self.seenstore = SeenStore(self.bot.store)
        self.started = datetime.timedelta(seconds=time.time())
        self.bot.add_event_handler("groupchat_presence",
                                   self.handle_groupchat_presence,
                                   threaded=True)
        self.bot.add_event_handler("groupchat_message",
                                   self.handle_groupchat_message,
                                   threaded=True)

    def handle_groupchat_presence(self, presence):
        """ Keep track of the presences in mucs.
        """
        if presence.get('type', None) == 'unavailable':
            ptype = SeenEvent.part_type
        else:
            ptype = SeenEvent.presence_type
        now = datetime.datetime.now()
        self.seenstore.update(SeenEvent(presence['from'].resource,
                                        now.strftime("%Y-%m-%d %H:%M:%S"),
                                        presence['from'].bare, ptype,
                                        presence.get('status', None)))

    def handle_groupchat_message(self, message):
        """ Keep track of activity through messages.
        """
        if 'body' not in message.keys():
            return
        now = datetime.datetime.now()
        self.seenstore.update(SeenEvent(message['from'].resource,
                                        now.strftime("%Y-%m-%d %H:%M:%S"),
                                        message['from'].bare,
                                        SeenEvent.message_type,
                                        message['body']))

    @botcmd('seen', usage='[nick]')
    def handle_seen_request(self, command, args, msg):
        """See when a user was last seen."""
        if args == None or args == "":
            return "Please supply a nickname to search for"
        seen_data = self.seenstore.get(args)
        if seen_data == None:
            return "I have never seen '" + args + "'"

        since_time_seconds = (datetime.datetime.now() - \
                            seen_data.event_time).seconds
        since_time = ""
        if since_time_seconds >= 3600:
            since_time = "%d hours ago" % (since_time_seconds / 3600)
        elif since_time_seconds >= 60:
            since_time = "%d minutes ago" % (since_time_seconds / 60)
        else:
            since_time = "%d seconds ago" % since_time_seconds
        status = ""
        if seen_data.stanza_type == SeenEvent.message_type:
            status = "saying '%s'" % seen_data.text
        elif seen_data.stanza_type == SeenEvent.presence_type and \
            seen_data.text is not None:
            status = "(%s)" % seen_data.text

        state = "in"
        if seen_data.stanza_type == SeenEvent.part_type:
            state = "leaving"
        #if seenData['show'] == None:
        #    state = "joining"
        return "'%s' was last seen %s %s %s %s" % \
                (args, state, seen_data.muc, since_time, status)
