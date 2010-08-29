"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

import logging
import datetime, time

from sleekbot.commandbot import botcmd
from sleekbot.plugbot import BotPlugin

class tell(BotPlugin):
    """A plugin to parrot text to a JID."""

    @botcmd(name = 'tell', usage = '[jid] [text]')
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