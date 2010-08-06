#!/usr/bin/env python
"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

__author__ = 'Hernan E. Grecco <hernan.grecco@gmail.com>'
__license__ = 'MIT License/X11 license'


import os
import time
import plugins
import sys
import logging

from store import store
from optparse import OptionParser
from xml.etree import ElementTree as ET

import sleekxmpp
from sleekxmpp.xmlstream.stanzabase import JID

from commandbot import  CommandBot
from plugbot import PlugBot

class SleekBot(sleekxmpp.ClientXMPP, CommandBot,  PlugBot):
    """ SleekBot was originally written by Nathan Fritz and Kevin Smith.
        This fork is maintained by Hernan E. Grecco
    """

    def __init__(self, config_file, ssl=False, plugin_config = {}):
        self.config_file = config_file
        self.botconfig = self.load_config(config_file)
        logging.info("Logging in as %s" % self.botconfig.find('auth').attrib['jid'])
        sleekxmpp.ClientXMPP.__init__(self, self.botconfig.find('auth').attrib['jid'],
                                      self.botconfig.find('auth').attrib['pass'], ssl, plugin_config)
        storageXml = self.botconfig.find('storage')
        if storageXml is not None:
            self.store = store(storageXml.attrib['file'])
        else:
            logging.warning("No storage element found in config file - proceeding with no persistent storage, plugin behaviour may be undefined.")
        self.rooms = {}
        self.add_event_handler("session_start", self.start, threaded=True)
        self.registerPlugin('xep_0030')
        self.registerPlugin('xep_0004')
        self.registerPlugin('xep_0045')
        self.registerPlugin('xep_0050')
        self.registerPlugin('xep_0060')
        self.registerPlugin('xep_0199')
        CommandBot.__init__(self)
        PlugBot.__init__(self)
        self.register_adhocs()

    def connect(self):
        auth = self.botconfig.find('auth')
        logging.info("Connecting ..." )
        if not auth.get('server', None):
            # we don't know the server, but the lib can probably figure it out
            super(SleekBot, self).ClientXMPP.connect()
        else:
            super(SleekBot, self).connect((auth.attrib['server'], auth.get('port', 5222)))


    def load_config(self, config_file = None):
        """ Load the specified config. Does not attempt to make changes based upon config.
        """
        if config_file:
            return ET.parse(config_file)
        else:
            return ET.parse(self.config_file)

    def register_adhocs(self):
        """ Register all ad-hoc commands with SleekXMPP.
        """
        aboutform = self.plugin['xep_0004'].makeForm('form', "About SleekBot")
        aboutform.addField('about', 'fixed', value= self.__doc__)
        self.plugin['xep_0050'].addCommand('about', 'About Sleekbot', aboutform)
        pluginform = self.plugin['xep_0004'].makeForm('form', 'Plugins')
        plugins = pluginform.addField('plugin', 'list-single', 'Plugins')
        for key in self.cmd_plugins:
            plugins.addOption(key, key)
        plugins = pluginform.addField('option', 'list-single', 'Commands')
        plugins.addOption('about', 'About')
        #plugins.addOption('config', 'Configure')
        self.plugin['xep_0050'].addCommand('plugins', 'Plugins', pluginform, self.form_plugin_command, True)

    def form_plugin_command(self, form, sessid):
        """ Take appropriate action when a plugin ad-hoc request is received.
        """
        value = form.getValues()
        option = value['option']
        plugin = value['plugin']
        if option == 'about':
            aboutform = self.plugin['xep_0004'].makeForm('form', "About SleekBot")
            aboutform.addField('about', 'fixed', value=getattr(self.cmd_plugins[plugin], 'about', self.cmd_plugins[plugin].__doc__))
            return aboutform, None, False
        elif option == 'config':
            pass

    def start(self, event):
        #TODO: make this configurable
        self.getRoster()
        self.sendPresence(ppriority = self.botconfig.find('auth').get('priority', '1'))
        self.join_rooms()

    def rehash(self):
        """ Re-reads the config file, making appropriate runtime changes.
            Causes all plugins to be reloaded (or unloaded). The XMPP stream, and
            channels will not be disconnected.
        """
        logging.info("Rehashing started")
        modules = self.cmd_plugins.get_modules()
        CommandBot.pause(self)
        PlugBot.stop(self)

        logging.info("Reloading config file")
        self.botconfig = self.load_config(self.config_file)
        for module in modules:
            reload(module)
        CommandBot.reset(self)

        PlugBot.start(self)
        CommandBot.resume(self)
        self.join_rooms()

    def join_rooms(self):
        logging.info("Re-syncing with required channels")
        xrooms = self.botconfig.findall('rooms/muc')
        rooms = {}
        for xroom in xrooms:
            rooms[xroom.attrib['room']] = xroom.attrib['nick']
        for room in set(self.rooms.keys()).difference(rooms.keys()):
            logging.info("Parting room %s." % room)
            self.plugin['xep_0045'].leaveMUC(room, self.rooms[room])
            del self.rooms[room]
        for room in set(rooms.keys()).difference(self.rooms.keys()):
            self.rooms[room] = rooms[room]
            logging.info("Joining room %s as %s." % (room, rooms[room]))
            self.plugin['xep_0045'].joinMUC(room, rooms[room])

    def die(self):
        """ Kills the bot.
        """
        PlugBot.stop(self)
        CommandBot.stop(self)
        self.rooms = {}
        logging.info("Disconnecting bot")
        self.disconnect()

    def restart(self):
        """ Cause the bot to be completely restarted (will reconnect etc.)
        """
        global shouldRestart
        shouldRestart = True
        logging.info("Restarting bot")
        self.die()

    #TODO: temporary until SleekXMPP is PEP8 compliant
    def send_message(self,  *args,  **kwargs):
        self.sendMessage(*args,  **kwargs)

if __name__ == '__main__':
    #parse command line arguements
    optp = OptionParser()
    optp.add_option('-q','--quiet', help='set logging to ERROR', action='store_const', dest='loglevel', const=logging.ERROR, default=logging.INFO)
    optp.add_option('-d','--debug', help='set logging to DEBUG', action='store_const', dest='loglevel', const=logging.DEBUG, default=logging.INFO)
    optp.add_option('-v','--verbose', help='set logging to COMM', action='store_const', dest='loglevel', const=5, default=logging.INFO)
    optp.add_option("-c","--config", dest="config_file", default="config.xml", help="set config file to use")
    opts,args = optp.parse_args()

    logging.basicConfig(level=opts.loglevel, format='%(levelname)-8s %(message)s')

    global shouldRestart
    shouldRestart = True
    while shouldRestart:
        shouldRestart = False
        logging.info("Loading config file: %s" % opts.config_file)

        plugin_config = {}
        plugin_config['xep_0092'] = {'name': 'SleekBot', 'version': '0.1-dev'}

        bot = SleekBot(opts.config_file, plugin_config=plugin_config)
        bot.connect()
        bot.process(threaded=False)
        while not bot.state['disconnecting']:
            time.sleep(1)
        #this does not work properly. Some thread is runnng

    logging.info("SleekBot finished")

