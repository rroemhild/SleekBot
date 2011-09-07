"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

__author__ = 'Hernan E. Grecco <hernan.grecco@gmail.com>'
__license__ = 'MIT License/X11 license'

import logging

from abc import ABCMeta, abstractproperty

from .pluginbase import PluginDict, Plugin


class BotPlugin(Plugin):
    """ Base class for plugins used with CommandBot
    """
    def __init__(self, *args, **kwargs):
        super(BotPlugin, self).__init__(*args, **kwargs)
        self.bot = None

    def _set_dict(self, value):
        if value is None:
            self.bot.unregister_commands(self)
        else:
            self.bot = value.bot
            self.bot.register_commands(self)
        super(BotPlugin, self)._set_dict(value)

    plugin_dict = property(fget=Plugin._get_dict, fset=_set_dict)


class PlugBot(object):
    """ Base class for bots that are pluggable
        Requires to be coinherited with a class that has a property named
            botconfig -- XML ElementTree from the config file. For example:
                <bot>
                    <plugin name='plugin1'>
                        <config />
                    </plugin>
                    <plugin name='plugin2' package='anotherpackage'>
                        <config />
                    </plugin>
                <bot>
    """
    __metaclass__ = ABCMeta

    def __init__(self, default_package='plugins'):
        """ Initialized the PlugBot by registering the plugins declared
            in botconfig
        """
        self.cmd_plugins = PluginDict(plugin_base_class=BotPlugin,
                                      default_package=default_package)
        self.cmd_plugins.bot = self

        PlugBot.start(self)

    @abstractproperty
    def botconfig(self):
        """ XML ElementTree from the config file
        """
        pass

    def register_cmd_plugins(self):
        """ Registers all bot plugins required by botconfig.
        """
        plugins = self.botconfig.findall('plugins/bot/plugin')
        if not plugins:
            return

        for plugin in plugins:
            atr = plugin.attrib
            loaded = self.cmd_plugins.register(atr['name'],
                                               plugin.find('config'),
                                               atr.get('module', None),
                                               atr.get('package', None))
            res = 'OK' if loaded else 'FAILED'
            logging.info('Registering plugin %s %s', atr['name'], res)

    def stop(self):
        """ Unregister command plugins
        """
        logging.info("Stopping PlugBot")
        for plugin in self.cmd_plugins.keys():
            del self.cmd_plugins[plugin]

    def start(self):
        """ Register command plugins
        """
        logging.info("Starting PlugBot")
        self.register_cmd_plugins()

    def reset(self):
        """  Reset PlugBot commands to its initial state
        """
        PlugBot.stop(self)
        PlugBot.start(self)
