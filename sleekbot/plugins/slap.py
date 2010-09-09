"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

import logging
import random

from sleekbot.commandbot import botcmd
from sleekbot.plugbot import BotPlugin

class slap(BotPlugin):
    """A plugin to smack people around with enormous iron bars and scary cellos."""
    
    def on_register(self):
        self.slap_verbs = self.config.find('verbs').text.split(',')
        self.slap_tools = self.config.find('tools').text.split(',')
        self.slap_size = self.config.find('size').text.split(',')
    
    @botcmd('slap', usage='[nickname]', IM=False)
    def handle_uptime(self, command, args, msg):
        """Smack people with enormous iron bars and scary cellos."""
        
        if args == None or args == '':
            return "Please supply a nickname."
        
        roster = self.bot.plugin['xep_0045'].getRoster(msg['mucroom'])
        
        for rosterNick in roster:
            if args.lower() == rosterNick.lower():
                
                nickRealJid = self.bot.mucnick_to_jid(msg['mucroom'], rosterNick)
                if nickRealJid != None:
                    if nickRealJid.bare in self.bot.owners:
                        return "I don't slap my owner!"
                
                # Do not slap the bot he will slap back
                if rosterNick == self.bot.plugin['xep_0045'].ourNicks[msg['mucroom']]:
                    rosterNick = msg['mucnick']
                
                return "/me %(verb)s %(nick)s with %(size)s %(tool)s." % {
                                'verb' : random.choice(self.slap_verbs),
                                'nick' : rosterNick,
                                'size' : random.choice(self.slap_size),
                                'tool' : random.choice(self.slap_tools)}
        
        return "Unkown nickname %s." % args
