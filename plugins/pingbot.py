"""
    pingbot.py - A plugin for pinging Jids.
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

from commandbot import botcmd
from plugbot import BotPlugin

class pingbot(BotPlugin):
    """Pingbot allows users to ping other jids.
    Written By: Kevin Smith"""    
               
    @botcmd(name = 'ping', usage = 'ping jid')
    def handle_ping(self, command, args, msg):
        """Discover latency to a jid."""
        latency = self.bot['xep_0199'].sendPing(args, 10)
        if latency == None:
            response = "No response when pinging " + args
        else:
            response = "Ping response received from %s in %d seconds." % (args, latency)
        return response