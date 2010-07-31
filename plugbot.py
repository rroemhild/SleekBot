#!/usr/bin/env python

import logging

from optparse import OptionParser
from xml.etree import ElementTree as ET

from pluginbase import PluginDict,  Plugin

class BotPlugin(Plugin):

    def _set_dict(self, value):
        if value is None:
            self.bot.unregister_commands(self)
        else:
            self.bot = value.bot
            super(BotPlugin,  self)._set_dict(value)
            self.bot.register_commands(self)

    plugin_dict = property(fget = Plugin._get_dict, fset = _set_dict)

class PlugBot(object):
    """ Base class for bots that are pluggable
        Requires to be coinherited with a class that has the following commands:
        - send_message
        - add_event_handler
        as defined in SleekXMPP
    """

    def __init__(self, default_package = 'plugins'):
        self.cmd_plugins = PluginDict(plugin_base_class = BotPlugin, default_package = default_package)
        self.cmd_plugins.bot = self

        PlugBot.start(self)

    def register_cmd_plugins(self):
        """ Registers all bot plugins required by botconfig.
        """
        plugins = self.botconfig.findall('plugins/bot/plugin')
        if plugins:
            for plugin in plugins:
                loaded = self.cmd_plugins.register(plugin.attrib['name'], plugin.find('config'))
                logging.info("Loading plugin %s ok" % (plugin.attrib['name']))
                if not loaded:
                    logging.info("Loading plugin %s FAILED." % (plugin.attrib['name']))

    def stop(self):
        logging.info("Stopping PlugBot")
        for plugin in self.cmd_plugins.keys():
            del self.cmd_plugins[plugin]

    def start(self):
        logging.info("Starting PlugBot")
        self.register_cmd_plugins()

    def reset(self):
        """  Reset commandbot commands to its initial state
        """
        PlugBot.stop(self)
        PlugBot.start(self)

        """ Causes all plugins to be reloaded (or unloaded).
        """
        #logging.info("Deregistering bot plugins for rehash")
        #globals()['plugins'] = __import__('plugins')
        #self.deregister_bot_plugins()
        #logging.info("Reloading config file")
        #self.register_cmd_plugins()
