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


class info(BotPlugin):
    """A plugin to obtain information about the bot."""

    def on_register(self):
        self.started = datetime.datetime.now()
        try:
            from guppy import hpy
            self.hpy = hpy()
        except:
            logging.warning("guppy not present. mem plugin not available")

    @botcmd()
    def uptime(self, command, args, msg):
        """See how long the bot has been up."""
        difference = datetime.datetime.now() - self.started
        weeks, days = divmod(difference.days, 7)
        minutes, seconds = divmod(difference.seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return "%s weeks %s days %s hours %s minutes %s seconds" % (weeks, days, hours, minutes, seconds)


    @botcmd('mem')
    def handle_mem(self, command, args, msg):
        """See how much memory python is using"""
        return '%s\n' % self.hpy.heap()

