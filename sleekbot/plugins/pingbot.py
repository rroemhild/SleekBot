"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

import logging

from sleekbot.commandbot import botcmd
from sleekbot.plugbot import BotPlugin

class pingbot(BotPlugin):
    """Pingbot allows users to ping other jids.
    Written By: Kevin Smith"""

    @botcmd(name = 'ping', usage = '[jid]')
    def handle_ping(self, command, args, msg):
        """Discover latency to a jid."""
        latency = self.bot['xep_0199'].sendPing(args, 10)
        if latency == None:
            response = "No response when pinging " + args
        else:
            response = "Ping response received from %s in %d seconds." % (args, latency)
        return response