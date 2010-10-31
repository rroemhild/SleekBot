"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

import random

from sleekbot.commandbot import botcmd, parse_args, ArgError
from sleekbot.plugbot import BotPlugin

""" Configuraton Example:
<plugin name="slap" module="fun">
    <config>
        <verbs>slaps,hits,smashes,beats,bashes,smacks,blats,
               punches,stabs</verbs>
        <size>a large,an enormous,a small,a tiny,a medium sized,
              an extra large,a questionable,a suspicious,a terrifying,
              a scary,a breath taking,a horrifying</size>
        <tools>trout,fork,mouse,piano,cello,vacuum,finetuned sledgehammer,
               sewing needle,Windows ME user guide,christmas tree,axe,
               iron bar,cello,set of Windows 3.11 floppies,MS IIS</tools>
    </config>
</plugin>
"""


class Slap(BotPlugin):
    """A plugin to smack people around with enormous iron bars and scary cellos.
    """

    def _on_register(self):
        """ Obtains verbs, tools and sizes from the config file """
        self.slap_verbs = self.config.find('verbs').text.split(',')
        self.slap_tools = self.config.find('tools').text.split(',')
        self.slap_size = self.config.find('size').text.split(',')

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
