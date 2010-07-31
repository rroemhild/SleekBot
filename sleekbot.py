#!/usr/bin/env python
"""
    This file is part of SleekXMPP.

    SleekXMPP is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    SleekXMPP is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with SleekXMPP; if not, write to the Free Software
    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""

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

class sleekbot(sleekxmpp.ClientXMPP, CommandBot,  PlugBot):
    """SleekBot was written by Nathan Fritz and Kevin Smith.
    SleekBot uses SleekXMPP which was also written by Nathan Fritz.
    http://sleekbot.googlecode.com
    -----------------------------------------------------------------
    Special thanks to David Search.
    Also, thank you Athena and Cath for putting up with us while we programmed."""

    def __init__(self, configFile, jid, password, ssl=False, plugin_config = {}):
        self.configFile = configFile
        self.botconfig = self.load_config(configFile)
        sleekxmpp.ClientXMPP.__init__(self, jid, password, ssl, plugin_config)
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
        #self.register_adhocs()

    def load_config(self, configFile):
        """ Load the specified config. Does not attempt to make changes based upon config.
        """
        return ET.parse(configFile)

    def register_adhocs(self):
        """ Register all ad-hoc commands with SleekXMPP.
        """
        aboutform = self.plugin['xep_0004'].makeForm('form', "About SleekBot")
        aboutform.addField('about', 'fixed', value= self.__doc__)
        self.plugin['xep_0050'].addCommand('about', 'About Sleekbot', aboutform)
        pluginform = self.plugin['xep_0004'].makeForm('form', 'Plugins')
        plugins = pluginform.addField('plugin', 'list-single', 'Plugins')
        for key in self.BotPlugin:
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
            aboutform.addField('about', 'fixed', value=getattr(self.BotPlugin[plugin], 'about', self.BotPlugin[plugin].__doc__))
            return aboutform, None, False
        elif option == 'config':
            pass

    def mucnick_to_jid(self, mucroom, mucnick):
        """ Returns the jid associated with a mucnick and mucroom
        """
        if mucroom in self.plugin['xep_0045'].getJoinedRooms():
            logging.debug("Checking real jid for %s %s" %(mucroom, mucnick))
            real_jid = self.plugin['xep_0045'].getJidProperty(mucroom, mucnick, 'jid')
            print real_jid
            if real_jid:
                return real_jid
            else:
                return None
        return None

    def get_real_jid(self, msg):
        if msg['type'] == 'groupchat':
            # TODO detect system message
            return self.mucnick_to_jid(msg['mucroom'], msg['mucnick']).bare
        else:
            if msg['jid'] in self['xep_0045'].getJoinedRooms():
                return self.mucnick_to_jid(msg['mucroom'], msg['mucnick']).bare
            else:
                return msg['from'].bare
        return None

    def start(self, event):
        #TODO: make this configurable
        self.getRoster()
        self.sendPresence(ppriority = self.botconfig.find('auth').get('priority', '1'))
        self.joinRooms()

    def rehash(self):
        """ Re-reads the config file, making appropriate runtime changes.
            Causes all plugins to be reloaded (or unloaded). The XMPP stream, and
            channels will not be disconnected.
        """
        logging.info("Rehashing started")
        modules = self.cmd_plugins.get_modules()
        CommandBot.stop(self)
        PlugBot.stop(self)
        logging.info("Reloading config file")
        self.botconfig = self.load_config(self.configFile)
        for module in modules:
            reload(module)
        CommandBot.start(self)
        PlugBot.start(self)
        self.joinRooms()

    def joinRooms(self):
        logging.info("Re-syncing with required channels")
        newRoomXml = self.botconfig.findall('rooms/muc')
        newRooms = {}
        if newRoomXml:
            for room in newRoomXml:
                newRooms[room.attrib['room']] = room.attrib['nick']
        for room in self.rooms.keys():
            if room not in newRooms.keys():
                logging.info("Parting room %s." % room)
                self.plugin['xep_0045'].leaveMUC(room, self.rooms[room])
                del self.rooms[room]
        for room in newRooms.keys():
            if room not in self.rooms.keys():
                self.rooms[room] = newRooms[room]
                logging.info("Joining room %s as %s." % (room, newRooms[room]))
                self.plugin['xep_0045'].joinMUC(room, newRooms[room])

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
        bot.process(threaded=False)
        while not bot.state['disconnecting']:
            time.sleep(1)
        #this does not work properly. Some thread is runnng

    logging.info("SleekBot finished")

