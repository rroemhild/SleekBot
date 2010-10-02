"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

import logging
import datetime, time

from sleekbot.commandbot import botcmd, CommandBot, denymsg, parse_args, ArgError
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

    @botcmd(usage = '[add | del | see | test] jid role', allow = CommandBot.msg_from_admin)
    def acl(self, command, args, msg):
        """ Access control list management
        """
        try:
            args = parse_args(args, ( ('action', ('add', 'del', 'see', 'test')), ('jid', str), ('role', 'user')))
        except ArgError as e:
            return e.msg

        return getattr(self, 'acl_' + args.action,)(command, args, msg)


    @botcmd(usage = 'jid role', allow = CommandBot.msg_from_admin, hidden = True)
    def acl_add(self, command, args, msg):
        """Add a jid with a given role
            If the user exists, modify the role.
        """
        try:
            args = parse_args(args, (('jid', str), ('role', 'user')))
        except ArgError as e:
            return e.msg

        try:
            rolen = getattr(self.bot.acl.ROLE, args.role)
        except:
            return '%s is not a valid role' % args.role

        present = args.jid in self.bot.acl
        self.bot.acl[args.jid] = rolen
        if present:
            return '%s updated as %s' % (args.jid, args.role)
        else:
            return '%s added as %s' % (args.jid, args.role)


    @botcmd(usage = 'jid', allow = CommandBot.msg_from_admin, hidden = True)
    def acl_del(self, command, args, msg):
        """Deletes a jid
        """
        try:
            args = parse_args(args, (('jid', str), ))
        except ArgError as e:
            return e.msg

        present = args.jid in self.bot.acl
        if present:
            del self.bot.acl[args.jid]
            return '%s deleted' % args.jid
        else:
            return '%s was not found in acl' % args.jid


    @botcmd(usage = 'jid', allow = CommandBot.msg_from_admin, hidden = True)
    def acl_see(self, command, args, msg):
        """See the role a jid
        """
        try:
            args = parse_args(args, (('jid', str), ))
        except ArgError as e:
            return e.msg

        p = self.bot.acl.find_part(args.jid)
        if p:
            if p == args.jid:
                return '%s is %s' % (args.jid, self.bot.acl.ROLE[self.bot.acl[args.jid]])
            else:
                return '%s through %s is %s' % (args.jid, p, self.bot.acl.ROLE[self.bot.acl[p]])
        else:
            return '%s was not found in acl' % args.jid


    @botcmd(usage = 'jid role', allow = CommandBot.msg_from_admin, hidden = True)
    def acl_test(self, command, args, msg):
        """Test if jid belongs to role
        """
        try:
            args = parse_args(args, (('jid', str), ('role', 'user')))
        except ArgError as e:
            return e.msg
        try:
            rolen = getattr(self.bot.acl.ROLE, args.role)
        except:
            return '%s is not a valid role' % args.role

        present = args.jid in self.bot.acl
        if present:
            if self.bot.acl.check(args.jid, rolen):
                return '%s is %s' % (args.jid, args.role)
            else:
                return '%s is not %s' % (args.jid, args.role)
        else:
            return '%s was not found in acl' % args.jid


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
