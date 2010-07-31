#!/usr/bin/env python

import logging

from optparse import OptionParser
from xml.etree import ElementTree as ET

from pluginbase import PluginDict,  Plugin

class BotPlugin(Plugin):
    
    def _set_dict(self, value):
        logging.info('set dict')
        self.bot = value.bot
        super(BotPlugin,  self)._set_dict (value)
        self.bot.register_commands(self)
    
    plugin_dict = property(fget = Plugin._get_dict, fset = _set_dict)

class PlugBot(object):
    """ Base class for bots that are pluggable
        Requires to be coinherited with a class that has the following commands:
        - send_message
        - add_event_handler
        as defined in SleekXMPP
    """
    
    def __init__(self):
        self.cmd_plugins = PluginDict(plugin_base_class = BotPlugin)
        self.cmd_plugins.bot = self
        self.register_cmd_plugins()

    def register_cmd_plugins(self):
        """ Registers all bot plugins required by botconfig.
        """
        plugins = self.botconfig.findall('plugins/bot/plugin')
        if plugins:
            for plugin in plugins:
                logging.info("Loading plugin %s." % (plugin.attrib['name']))
                loaded = self.cmd_plugins.register(plugin.attrib['name'], plugin.find('config'))
                if not loaded:
                    logging.info("Loading plugin %s FAILED." % (plugin.attrib['name']))

    def reset(self):
        """ Causes all plugins to be reloaded (or unloaded). 
        """
        logging.info("Deregistering bot plugins for rehash")
        globals()['plugins'] = __import__('plugins')
        #self.deregister_bot_plugins()
        logging.info("Reloading config file")
        self.register_cmd_plugins()
