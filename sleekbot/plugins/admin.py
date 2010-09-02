"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

import logging

from sleekbot.commandbot import botcmd, CommandBot, denymsg
from sleekbot.plugbot import BotPlugin

class admin(BotPlugin):
    """ Plugin to allows a bot owner to perform tasks such as rehashing a bot remotely
    """

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
