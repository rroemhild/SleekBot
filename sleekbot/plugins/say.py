"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

import logging
import datetime, time

from commandbot import botcmd
from plugbot import BotPlugin

class say(BotPlugin):
    """A plugin to parrots text to a muc"""

    @botcmd(name = 'say', usage = '[muc] [text]')
    def handle_say(self, command, args, msg):
        """Have the bot parrot some text in a channel."""

        if not self.bot.msg_from_owner(msg):
            return "I'm not your monkey."
        if args.count(" ") >= 1:
            [muc, text] = args.split(" ",1)
        else:
            return "Insufficient parameters."
        self.bot.sendMessage(muc, text, mtype='groupchat')
        return "Sent."