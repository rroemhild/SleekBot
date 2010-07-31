"""
    say.py - A plugin for making a bot parrot text.
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
import datetime, time

from commandbot import botcmd
from plugbot import BotPlugin

class tell(BotPlugin):
    """A plugin to parrot text to a JID."""

    @botcmd(name = 'tell', usage = 'tell jid text')
    def handle_tell(self, command, args, msg):
        """Have the bot parrot some text to a JID."""
        if not self.bot.msg_from_owner(msg):
            return "I'm not your monkey."
        if args.count(" ") >= 1:
            [jid, text] = args.split(" ",1)
        else:
            return "Insufficient parameters."
        self.bot.sendMessage(jid, text, mtype='chat')
        return "Sent."