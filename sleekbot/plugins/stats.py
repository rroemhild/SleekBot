"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""


import logging
import datetime
from operator import itemgetter

from sleekbot.commandbot import botcmd, botfreetxt, CommandBot
from sleekbot.commandbot import parse_args, ArgError
from sleekbot.plugbot import BotPlugin


class CmdEvent(object):
    """ Represent an bot command event
    """

    imMessage = 0
    mucMessage = 1

    def __init__(self, cmd, args, mtype, timestamp):
        """ Initialise aliascmd
        """

        self.cmd = cmd
        self.args = args
        self.type = mtype
        self.time = timestamp


class CmdStore(object):
    """ Class to store used command in the database.
    """

    def __init__(self, store):
        self.store = store
        self.create_table()

    def create_table(self):
        """ Create the cmdstore table."""

        with self.store.context_cursor() as cur:
            if not self.store.has_table(cur, 'stats_botcmd'):
                cur.execute("""CREATE TABLE "stats_botcmd" (
                            "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                            "cmd" VARCHAR(256), "args" VARCHAR(256),
                            "type" INTEGER,
                            "time" DATETIME)""")
                logging.debug("stats table created")

    def insert(self, event):
        """ Insert a command usage."""
        
        with self.store.context_cursor() as cur:
            cur.execute('INSERT INTO stats_botcmd(cmd, args, type, time)' \
             'VALUES(?,?,?,?)', (event.cmd, event.args, event.type, event.time))

    def get(self, cmd):
        """ Get command usage statistic."""
        
        with self.store.context_cursor() as cur:
            cur.execute('SELECT count(*) FROM stats_botcmd WHERE cmd=?', (cmd,))
            return str(cur.fetchone()[0])

    def get_all(self):
        """ Get all command usage statistics."""
        
        with self.store.context_cursor() as cur:
            cur.execute('SELECT * FROM stats_botcmd')
            results = cur.fetchall()
            if len(results) == 0:
                return None
            response = []
            for result in results:
                response.append(CmdEvent(result[1], result[2],
                                    result[3], result[4]))
            return response


class CmdStats(BotPlugin):
    """A Plugin for logging command usage to the database."""

    freetextRegex = ''

    def _on_register(self):
        """ Create regular expression. """
        self.chat_prefix = self.bot.chat_prefix
        self.muc_prefix = self.bot.muc_prefix
        self.cmd_store = CmdStore(self.bot.store)

        # botfreetext regex string with im and mux prefix
        global freetextRegex
        freetextRegex = "^[\%s\%s][a-zA-Z].*$" \
            % (self.chat_prefix, self.muc_prefix)

    @botfreetxt(priority=100, regex=freetextRegex)
    def commandevent(self, text, msg, command_found, freetext_found, match):
        """ Match a freetext muc or im command and store it to the
        database.
        """

        if not command_found:
            return

        if msg['type'] == 'groupchat':
            prefix = self.muc_prefix
            msg_type = CmdEvent.mucMessage
        else:
            prefix = self.chat_prefix
            msg_type = CmdEvent.imMessage
        command = msg.get('body', '').strip().split(' ', 1)[0]
        if ' ' in msg.get('body', ''):
            args = msg['body'].split(' ', 1)[-1].strip()
        else:
            args = ''
        if command.startswith(prefix):
            if len(prefix):
                command = command.split(prefix, 1)[-1]

        now = datetime.datetime.now()
        self.cmd_store.insert(CmdEvent(command, args, msg_type,
                                now.strftime("%Y-%m-%d %H:%M:%S")))


class Stats(BotPlugin):
    """A plugin to obtain statistics and information about the bot."""

    def _on_register(self):
        """ Create CmdStore """
        self.cmd_store = CmdStore(self.bot.store)

    @botcmd(usage='[cmd]', allow=CommandBot.msg_from_owner)
    def stats(self, command, args, msg):
        """ Get command usage statistics."""
        
        try:
            args = parse_args(args, (('cmd', ''), ))
        except ArgError as error:
            return error.msg

        if args.cmd:
            result = self.cmd_store.get(args.cmd)
            if result:
                return "%s: %s" % (args, result)
            else:
                return "No stats for command %s." % args

        results = self.cmd_store.get_all()
        cmd_stats = {}
        if not results is None:
            for stat in results:
                if cmd_stats.has_key(stat.cmd):
                    cmd_stats[stat.cmd] += 1
                else:
                    cmd_stats[stat.cmd] = 1

        cmd_list = []
        for (key, val) in cmd_stats.iteritems():
            cmd_list.append({'cmd': key, 'count': val})

        cmd_stats = sorted(cmd_list, key=itemgetter('count'), reverse=True)

        response = "Command usage:\n"
        for stat in cmd_stats:
            response += "%s: %s\n" % (stat['count'], stat['cmd'])
        return response


class Info(BotPlugin):
    """A plugin to obtain information about the bot."""

    def __init__(self, *args, **kwargs):
        try:
            from guppy import hpy
            self.hpy = hpy()
        except:
            delattr(Info, 'mem')
            logging.warning("guppy not present. mem plugin not available")
        super(Info, self).__init__(*args, **kwargs)
        self.started = False

    def _on_register(self):
        """ Starting time. """
        self.started = datetime.datetime.now()

    @botcmd()
    def uptime(self, command, args, msg):
        """ See how long the bot has been up."""

        difference = datetime.datetime.now() - self.started
        weeks, days = divmod(difference.days, 7)
        minutes, seconds = divmod(difference.seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return "%s weeks %s days %s hours %s minutes %s seconds" % \
                (weeks, days, hours, minutes, seconds)

    @botcmd(allow=CommandBot.msg_from_owner)
    def mem(self, command, args, msg):
        """ See how much memory python is using."""

        return '%s\n' % self.hpy.heap()
