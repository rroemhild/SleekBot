"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

import logging
import datetime, time

from sleekbot.commandbot import botcmd, CommandBot, denymsg
from sleekbot.plugbot import BotPlugin

class admin(BotPlugin):
    """A plugin to allows a bot owner to perform tasks such as rehashing a bot remotely."""

    @botcmd(name = 'rehash', allow=CommandBot.msg_from_owner)
    @denymsg('You are insufficiently cool, go away')
    def handle_rehash(self, command, args, msg):
        """ Reload the bot config and plugins without dropping the XMPP stream."""

        self.bot.rehash()
        return "Rehashed boss"

    @botcmd(name = 'restart', allow=CommandBot.msg_from_owner)
    @denymsg('You are insufficiently cool, go away')
    def handle_restart(self, command, args, msg):
        """ Restart the bot, reconnecting, etc ..."""

        self.bot.restart()
        return "Restarted boss"

    @botcmd(name = 'die', allow=CommandBot.msg_from_owner)
    @denymsg('You are insufficiently cool, go away')
    def handle_die(self, command, args, msg):
        """ Kill the bot."""

        self.bot.die()
        return "Dying (you'll never see this message)"

    @botcmd(name = 'reload', allow=CommandBot.msg_from_owner)
    def handle_reload(self, command, args, msg):
        """ Reload the plugins """

        self.bot.cmd_plugins.reload_all()
        return "Reloaded boss"

class acl(BotPlugin):
    """ Allows managing users"""

    @botcmd(usage = 'jid role', allow = CommandBot.msg_from_admin)
    def acl_add(self, command, args, msg):
        """Add a jid with a given role
            If the user exists, modify the role.
        """
        (jid, role) = args.split(' ')
        try:
            rolen = getattr(self.bot.acl.ROLE, role)
        except:
            return '%s is not a valid role' % role

        present = jid in self.bot.acl
        self.bot.acl[jid] = rolen
        if present:
            return '%s updated as %s' % (jid, role)
        else:
            return '%s added as %s' % (jid, role)


    @botcmd(usage = 'jid', allow = CommandBot.msg_from_admin)
    def acl_del(self, command, args, msg):
        """Deletes a jid
        """
        jid = args.strip()

        present = jid in self.bot.acl
        if present:
            del self.bot.acl[jid]
            return '%s deleted' % jid
        else:
            return '%s was not found in acl' % jid


    @botcmd(usage = 'jid', allow = CommandBot.msg_from_admin)
    def acl_see(self, command, args, msg):
        """See the role a jid
        """
        jid = args.strip()

        p = self.bot.acl.find_part(jid)
        if p:
            if p == jid:
                return '%s is a %s' % (jid, self.bot.acl.ROLE[self.bot.acl[jid]])
            else:
                return '%s through %s is %s' % (jid, p, self.bot.acl.ROLE[self.bot.acl[p]])
        else:
            return '%s was not found in acl' % jid


    @botcmd(usage = 'jid role', allow = CommandBot.msg_from_admin)
    def acl_test(self, command, args, msg):
        """Test if jid belongs to role
        """
        (jid, role) = args.split(' ')
        try:
            rolen = getattr(self.bot.acl.ROLE, role)
        except:
            return '%s is not a valid role' % role

        present = jid in self.bot.acl
        if present:
            if self.bot.acl.check(jid, rolen):
                return '%s is %s' % (jid, role)
            else:
                return '%s is not %s' % (jid, role)
        else:
            return '%s was not found in acl' % jid


class info(BotPlugin):
    """A plugin to obtain information about the bot."""

    def __init__(self, *args, **kwargs):
        try:
            from guppy import hpy
            self.hpy = hpy()
        except:
            delattr(info, 'mem')
            logging.warning("guppy not present. mem plugin not available")
        super(info, self).__init__(*args, **kwargs)


    def on_register(self):
        self.started = datetime.datetime.now()


    @botcmd()
    def uptime(self, command, args, msg):
        """See how long the bot has been up."""
        difference = datetime.datetime.now() - self.started
        weeks, days = divmod(difference.days, 7)
        minutes, seconds = divmod(difference.seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return "%s weeks %s days %s hours %s minutes %s seconds" % (weeks, days, hours, minutes, seconds)


    @botcmd(allow=CommandBot.msg_from_owner)
    def mem(self, command, args, msg):
        """See how much memory python is using"""
        return '%s\n' % self.hpy.heap()
