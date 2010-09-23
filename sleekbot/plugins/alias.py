"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

""" Configuration example
<!-- <alias /> is optinal and for global aliases. Alias specified by
the user has precedence. -->
<plugin name="alias">
    <config>
        <alias name="r" command="rehash" />
        <alias name="r100" command="random 100" />
        <alias name="say2muc" command="say c1@conference.localhost" />
    </config>
</plugin>
"""

import re
import logging

from sleekbot.commandbot import botcmd, botfreetxt
from sleekbot.plugbot import BotPlugin

class aliascmd(object):
    """ Represent an aliased command
    """

    def __init__(self, jid, alias, command=None):
        """ Initialise aliascmd
        """

        self.jid = jid
        self.alias = alias
        self.command = command

class aliasstore(object):
    def __init__(self, store):
        self.store = store
        self.createTable()

    def createTable(self):
        db = self.store.getDb()
        if not len(db.execute("pragma table_info('alias')").fetchall()) > 0:
            db.execute("""CREATE TABLE "alias" ("id" INTEGER PRIMARY KEY AUTOINCREMENT,
                                       "jid" TEXT NOT NULL, "alias" TEXT NOT NULL,
                                       "command" TEXT NOT NULL)""")
        db.close()

    def update(self, alias):
        db = self.store.getDb()
        cur = db.cursor()
        cur.execute('SELECT * FROM alias WHERE jid=? AND alias=?', (alias.jid, alias.alias))
        if (len(cur.fetchall()) > 0):
            cur.execute('UPDATE alias SET jid=?, command=?, alias=? WHERE jid=? AND alias=?', (alias.jid, alias.command, alias.alias, alias.jid, alias.alias))
        else:
            cur.execute('INSERT INTO alias(jid, command, alias) VALUES(?,?,?)', (alias.jid, alias.command, alias.alias))
        db.commit()
        db.close()

    def get(self, alias):
        db = self.store.getDb()
        cur = db.cursor()
        cur.execute('SELECT * FROM alias WHERE jid=? AND alias=?', (alias.jid, alias.alias))
        results = cur.fetchall()
        if len(results) == 0:
            return None
        return aliascmd(results[0][1],results[0][2],results[0][3])
        db.close()

    def get_all(self, jid):
        db = self.store.getDb()
        cur = db.cursor()
        cur.execute('SELECT * FROM alias WHERE jid=?', (jid,))
        results = cur.fetchall()
        if len(results) == 0:
            return None
        response = []
        for result in results:
            response.append(aliascmd(result[1],result[2],result[3]))
        return response

    def delete(self, alias):
        db = self.store.getDb()
        cur = db.cursor()
        cur.execute('DELETE FROM alias WHERE jid=? AND alias=?', (alias.jid, alias.alias))
        db.commit()
        db.close()

class alias(BotPlugin):
    """ A plugin for global and user defined aliases.
    """

    freetextRegex = ''

    def on_register(self):
        self.im_prefix = self.bot.im_prefix
        self.muc_prefix = self.bot.muc_prefix
        self.aliasstore = aliasstore(self.bot.store)

        # botfreetext regex string with im and mux prefix
        global freetextRegex
        freetextRegex = "^[\%s\%s][a-zA-Z].*$" % (self.im_prefix,
                                                  self.muc_prefix)

        # global aliases
        self.global_aliases = {}
        if self.config:
            for alias in self.config.findall('alias'):
                logging.debug("Load global alias: %s" % alias.attrib['name'])
                self.global_aliases[alias.attrib['name']] = aliascmd(None,
                                                  alias.attrib['name'],
                                                  alias.attrib['command'])

    @botfreetxt(priority=1, regex=freetextRegex)
    def handle_alias(self, text, msg, command_found, freetext_found, match):
        """ Botfreetext handler that match global or user defined
            aliases. The aliased command replaces the msg['body']
            which is then routed again to self.bot.handle_msg_botcmd(msg).
        """

        if command_found is True:
            return
        if msg['type'] == 'groupchat':
            prefix = self.muc_prefix
        else:
            prefix = self.im_prefix
        command = msg.get('body', '').strip().split(' ', 1)[0]
        if ' ' in msg.get('body', ''):
            args = msg['body'].split(' ', 1)[-1].strip()
        else:
            args = ''
        if command.startswith(prefix):
            if len(prefix):
                command = command.split(prefix, 1)[-1]
            alias = self.aliasstore.get(aliascmd(self.bot.get_real_jid(msg), command))
            if not alias is None:
                msg['body'] = "%s%s %s" % (prefix, alias.command, args)
                self.bot.handle_msg_botcmd(msg)
            elif self.global_aliases.has_key(command):
                alias = self.global_aliases[command]
                msg['body'] = "%s%s %s" % (prefix, alias.command, args)
                self.bot.handle_msg_botcmd(msg)

    @botcmd(usage='[list|add|delete] [alias] [command] [options]')
    def alias(self, command, args, msg):
        """Replace long commands (incl. options) with short words."""

        if args.count(" ") > 0:
            (option, value) = args.split(" ", 1)
        else:
            (option, value) = (args, None)
        options = ['list', 'add', 'delete']

        if not option in options:
            return "Please supply an option."

        if option == 'add' and not value is None:
            if value.count(" ") < 1:
                return "Please supply a command for the alias."
            (alias, cmd) = value.split(' ', 1)
            self.aliasstore.update(aliascmd(self.bot.get_real_jid(msg), alias, cmd))
            return "Done."

        if option == 'delete':
            alias = self.aliasstore.get(aliascmd(self.bot.get_real_jid(msg), value))
            if not alias is None:
                self.aliasstore.delete(aliascmd(self.bot.get_real_jid(msg), value))
                return "Done."
            if self.global_aliases.has_key(value):
                return "You can not delete a global alias."
            return "Unkown alias."

        if option == 'list':
            aliases = self.aliasstore.get_all(self.bot.get_real_jid(msg))
            response = 'Aliases: '
            if not aliases is None:
                for alias in aliases:
                    response += "\n%s = %s" % (alias.alias, alias.command)
            if not self.global_aliases == {}:
                for key,alias in self.global_aliases.iteritems():
                    response += "\n(*) %s = %s" % (alias.alias, alias.command)
            if response == 'Aliases: ':
                response += "None."
            return response
