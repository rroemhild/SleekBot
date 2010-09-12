"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

import logging
import datetime, time

from sleekbot.commandbot import botcmd
from sleekbot.plugbot import BotPlugin

class others(BotPlugin):
    """A plugin to interact with and obtain information about other users."""

    @botcmd(usage = '[muc] [text]')
    def say(self, command, args, msg):
        """Have the bot parrot some text in a channel."""

        if not self.bot.msg_from_owner(msg):
            return "I'm not your monkey."
        if args.count(" ") >= 1:
            [muc, text] = args.split(" ",1)
        else:
            return "Insufficient parameters."
        self.bot.sendMessage(muc, text, mtype='groupchat')
        return "Sent."


    @botcmd(usage = '[jid] [text]')
    def tell(self, command, args, msg):
        """Have the bot parrot some text to a JID."""
        if not self.bot.msg_from_owner(msg):
            return "I'm not your monkey."
        if args.count(" ") >= 1:
            [jid, text] = args.split(" ",1)
        else:
            return "Insufficient parameters."
        self.bot.sendMessage(jid, text, mtype='chat')
        return "Sent."


    @botcmd(usage = '[jid]')
    def ping(self, command, args, msg):
        """Discover latency to a jid."""
        latency = self.bot['xep_0199'].sendPing(args, 10)
        if latency == None:
            response = "No response when pinging " + args
        else:
            response = "Ping response received from %s in %d seconds." % (args, latency)
        return response