"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

import random

from sleekbot.commandbot import botcmd, parse_args, ArgError
from sleekbot.plugbot import BotPlugin

class Slap(BotPlugin):
    """A plugin to smack people around with enormous iron bars and scary cellos.
    """
    DEFAULT_VERBS = 'slaps,hits,smashes,beats,bashes,smacks,blats,punches,stabs'
    DEFAULT_SIZE = ('a large,an enormous,a small,a tiny,a medium sized,' 
                    'an extra large,a questionable,a suspicious,a terrifying,' 
                    'a scary,a breath taking,a horrifying')
    DEFAULT_TOOLS = ('trout,fork,mouse,piano,cello,vacuum,finetuned sledgehammer,'
                     'sewing needle,Windows ME user guide,christmas tree,axe,'
                     'iron bar,cello,set of Windows 3.11 floppies,MS IIS')
    
    def __init__(self, verbs=Slap.DEFAULT_VERBS, size=Slap.DEFAULT_SIZE,
                 tools=Slap.DEFAULT_TOOLS):
        BotPlugin.__init__(self)
        self.slap_verbs = [v.strip() for v in verbs.split(',')]
        self.slap_tools = [t.strip() for t in tools.split(',')]
        self.slap_size = [s.strip() for s in size.split(',')]      

    @botcmd(usage='[nickname]', chat=False)
    def slap(self, command, args, msg):
        """Smack people with enormous iron bars and scary cellos."""

        try:
            args = parse_args(args, (('nickname', str), ))
        except ArgError as error:
            return error.msg
            
        room = msg['mucroom']

        roster = self.bot.plugin['xep_0045'].getRoster(room)

        for roster_nick in roster:
            if args.lower() == roster_nick.lower():

                nick_real_jid = self.bot.mucnick_to_jid(room, 
                                                        roster_nick)
                if nick_real_jid != None:
                    if nick_real_jid.bare in self.bot.acl.owners:
                        return "I don't slap my owner!"

                # Do not slap the bot he will slap back
                if roster_nick == self.bot.plugin['xep_0045'].ourNicks[room]:
                    roster_nick = msg['mucnick']

                return "/me %(verb)s %(nick)s with %(size)s %(tool)s." % {
                                'verb': random.choice(self.slap_verbs),
                                'nick': roster_nick,
                                'size': random.choice(self.slap_size),
                                'tool': random.choice(self.slap_tools)}

        return "Unknown nickname %s." % args
