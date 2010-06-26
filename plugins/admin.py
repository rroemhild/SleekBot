"""
    admin.py - A plugin for administering the bot.
    Copyright (C) 2007 Kevin Smith

    SleekBot is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    SleekBot is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this software; if not, write to the Free Software
    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""

import logging

from basebot import botcmd, botplugin

class admin(botplugin):
    """ Plugin to allows a bot owner to perform tasks such as rehashing a bot remotely
    Written By: Kevin Smith"""

    @botcmd(name = 'rehash')
    def handle_rehash(self, command, args, msg):
        """ Reload the bot config and plugins without dropping the XMPP stream."""
        if self.bot.message_from_owner(msg):
            self.bot.rehash()
            response = "Rehashed boss"
        else:
            response = "You are insufficiently cool, go away."
        return response

    @botcmd(name = 'restart')
    def handle_restart(self, command, args, msg):
        """ Restart the bot, reconnecting, etc ..."""
        if self.bot.message_from_owner(msg):
            self.bot.restart()
            response = "Restarted boss"
        else:
            response = "You are insufficiently cool, go away."
        return response

    @botcmd(name = 'die')
    def handle_die(self, command, args, msg):
        """ Kill the bot."""
        if self.bot.message_from_owner(msg):
            response = "Dying (you'll never see this message)"
            self.bot.die()
        else:
            response = "You are insufficiently cool, go away."
        return response
