#!/usr/bin/env python

import logging

from optparse import OptionParser
from xml.etree import ElementTree as ET

from pluginbase import PluginDict

class BotPlugin(object):
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.bot.register_botcmd(self)

class PlugBot(object):
    """ Base class for bots that are pluggable
        Requires to be coinherited with a class that has the following commands:
        - send_message
        - add_event_handler
        as defined in SleekXMPP
    """
    
    def __init__(self):
        self.cmd_plugins = plugin_dict(plugin_base = BotPlugin)
        self.register_bot_plugins()

    def register_bot_plugins(self):
        """ Registers all bot plugins required by botconfig.
        """
        plugins = self.botconfig.findall('plugins/bot/plugin')
        if plugins:
            for plugin in plugins:
                logging.info("Loading plugin %s." % (plugin.attrib['name']))
                loaded = self.registerBotPlugin(plugin.attrib['name'], plugin.find('config'))
                if not loaded:
                    logging.info("Loading plugin %s FAILED." % (plugin.attrib['name']))

    def rehash(self):
        """ Re-reads the config file, making appropriate runtime changes.
            Causes all plugins to be reloaded (or unloaded). The XMPP stream, and
            channels will not be disconnected.
        """
        logging.info("Deregistering bot plugins for rehash")
        del globals()['plugins']
        globals()['plugins'] = __import__('plugins')
        self.reset_bot()
        self.deregister_bot_plugins()
        logging.info("Reloading config file")
        self.botconfig = self.loadConfig(self.configFile)
        self.register_bot_plugins()
        self.joinRooms()

if __name__ == '__main__':
    #parse command line arguements
    optp = OptionParser()
    optp.add_option('-q','--quiet', help='set logging to ERROR', action='store_const', dest='loglevel', const=logging.ERROR, default=logging.INFO)
    optp.add_option('-d','--debug', help='set logging to DEBUG', action='store_const', dest='loglevel', const=logging.DEBUG, default=logging.INFO)
    optp.add_option('-v','--verbose', help='set logging to COMM', action='store_const', dest='loglevel', const=5, default=logging.INFO)
    optp.add_option("-c","--config", dest="configfile", default="config.xml", help="set config file to use")
    opts,args = optp.parse_args()

    logging.basicConfig(level=opts.loglevel, format='%(levelname)-8s %(message)s')

    global shouldRestart
    shouldRestart = True
    while shouldRestart:
        shouldRestart = False
        #load xml config
        logging.info("Loading config file: %s" % opts.configfile)
        configFile = os.path.expanduser(opts.configfile)
        config = ET.parse(configFile)
        auth = config.find('auth')

        #init
        logging.info("Logging in as %s" % auth.attrib['jid'])

        plugin_config = {}
        plugin_config['xep_0092'] = {'name': 'SleekBot', 'version': '0.1-dev'}

        bot = sleekbot(configFile, auth.attrib['jid'], auth.attrib['pass'], plugin_config=plugin_config)
        if not auth.get('server', None):
            # we don't know the server, but the lib can probably figure it out
            bot.connect()
        else:
            bot.connect((auth.attrib['server'], 5222))
        bot.process()
        while bot.state['connected']:
            time.sleep(1)
