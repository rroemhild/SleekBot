"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

import logging

from sleekbot.commandbot import botcmd
from sleekbot.plugbot import BotPlugin

MASK = """<message><event xmlns='http://jabber.org/protocol/pubsub#event'>
<items node='http://jabber.org/protocol/tune' /></event></message>"""

FIND = '{http://jabber.org/protocol/pubsub#event}event/' + \
       '{http://jabber.org/protocol/pubsub#event}item/' + \
       '{http://jabber.org/protocol/tune}tune'

FEATURE = 'http://jabber.org/protocol/tune+notify'

class GetTune(BotPlugin):
    """A plugin to get user tune info."""

    def _on_register(self):
        """ Register tunes into disco service plugin """
        self.bot.plugin['xep_0030'].add_feature(FEATURE)
        self.bot.add_handler(MASK, self.handle_tune)
        self.tunes = {}

    def handle_tune(self, xml):
        """ Store a tune.
        """
        logging.info("Got Tune")
        jid = xml.get('from')
        tune = xml.find(FIND)
        if tune is None:
            self.tunes[jid] = 'No tune.'
            return
        artist = tune.find('{http://jabber.org/protocol/tune}artist')
        if artist is None:
            artist = 'No Artist'
        else:
            artist = artist.text
        title = tune.find('{http://jabber.org/protocol/tune}title')
        if title is None:
            title = 'No Title'
        else:
            title = title.text
        self.tunes[jid] = "%s - %s" % (artist, title)

    @botcmd(name='gettune')
    def handle_gettune(self, cmd, args, msg):
        """ Returns the published tunes.
        """
        if not args:
            output = []
            for jid in self.tunes:
                output.append("%s: %s" % (jid, self.tunes[jid]))
            output = '\n'.join(output)
        else:
            output = self.tunes.get(args[0], 'No tune published.')
        return output
