"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

import logging

from commandbot import botcmd
from plugbot import BotPlugin

class admin(BotPlugin):
    """ Plugin to allows a bot owner to perform tasks such as rehashing a bot remotely
    Written By: Kevin Smith"""

    @botcmd(name = 'rehash')
    def handle_rehash(self, command, args, msg):
        """ Reload the bot config and plugins without dropping the XMPP stream."""
        if self.bot.msg_from_owner(msg):
            self.bot.rehash()
            response = "Rehashed boss"
        else:
            response = "You are insufficiently cool, go away."
        return response

    @botcmd(name = 'restart')
    def handle_restart(self, command, args, msg):
        """ Restart the bot, reconnecting, etc ..."""
        if self.bot.msg_from_owner(msg):
            self.bot.restart()
            response = "Restarted boss"
        else:
            response = "You are insufficiently cool, go away."
        return response

    @botcmd(name = 'die')
    def handle_die(self, command, args, msg):
        """ Kill the bot."""
        if self.bot.msg_from_owner(msg):
            response = "Dying (you'll never see this message)"
            self.bot.die()
        else:
            response = "You are insufficiently cool, go away."
        return response

    @botcmd(name = 'reload')
    def handle_reload(self, command, args, msg):
        """ Reload the plugins """
        if self.bot.msg_from_owner(msg):
            self.bot.cmd_plugins.reload_all()
            response = "Reloaded boss"
        else:
            response = "You are insufficiently cool, go away."
        return response
