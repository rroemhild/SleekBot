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

from basebot import basebot

class sleekbot(sleekxmpp.ClientXMPP, basebot):
    """SleekBot was written by Nathan Fritz and Kevin Smith.
    SleekBot uses SleekXMPP which was also written by Nathan Fritz.
    http://sleekbot.googlecode.com
    -----------------------------------------------------------------
    Special thanks to David Search.
    Also, thank you Athena and Cath for putting up with us while we programmed."""

    def __init__(self, configFile, jid, password, ssl=False, plugin_config = {}):
        self.configFile = configFile
        self.botconfig = self.loadConfig(configFile)
        sleekxmpp.ClientXMPP.__init__(self, jid, password, ssl, plugin_config)
        basebot.__init__(self)
        storageXml = self.botconfig.find('storage')
        if storageXml is not None:
            self.store = store(storageXml.attrib['file'])
        else:
            logging.warning("No storage element found in config file - proceeding with no persistent storage, plugin behaviour may be undefined.")
        self.rooms = {}
        self.botPlugin = {}
        self.pluginConfig = {}
        self.add_event_handler("session_start", self.start, threaded=True)
        self.registerPlugin('xep_0030')
        self.registerPlugin('xep_0004')
        self.registerPlugin('xep_0045')
        self.registerPlugin('xep_0050')
        self.registerPlugin('xep_0060')
        self.registerPlugin('xep_0199')
        self.register_bot_plugins()
        self.registerCommands()
        self.owners = set(self.getMemberClassJids('owner'))
        self.admins = set(self.getMemberClassJids('admin'))
        self.members = set(self.getMemberClassJids('member'))
        self.banned = set(self.getMemberClassJids('banned'))

    def loadConfig(self, configFile):
        """ Load the specified config. Does not attempt to make changes based upon config.
        """
        return ET.parse(configFile)

    def registerCommands(self):
        """ Register all ad-hoc commands with SleekXMPP.
        """
        aboutform = self.plugin['xep_0004'].makeForm('form', "About SleekBot")
        aboutform.addField('about', 'fixed', value= self.__doc__)
        self.plugin['xep_0050'].addCommand('about', 'About Sleekbot', aboutform)
        pluginform = self.plugin['xep_0004'].makeForm('form', 'Plugins')
        plugins = pluginform.addField('plugin', 'list-single', 'Plugins')
        for key in self.botPlugin:
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
            aboutform.addField('about', 'fixed', value=getattr(self.botPlugin[plugin], 'about', self.botPlugin[plugin].__doc__))
            return aboutform, None, False
        elif option == 'config':
            pass

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

    def deregister_bot_plugins(self):
        """ Unregister all loaded bot plugins.
        """
        for plugin in self.botPlugin.keys():
            self.deregisterBotPlugin(plugin)

    def plugin_name_to_module(self, pluginname):
        """ Takes a plugin name, and returns a module name
        """
        #following taken from sleekxmpp.py
        # discover relative "path" to the plugins module from the main app, and import it.
        return "%s.%s" % (globals()['plugins'].__name__, pluginname)

    def deregisterBotPlugin(self, pluginName):
        """ Unregisters a bot plugin.
        """
        logging.info("Unloading plugin %s" % pluginName)
        if hasattr(self.botPlugin[pluginName], 'shutDown'):
            logging.debug("Plugin has a shutDown() method, so calling that.")
            self.botPlugin[pluginName].shutDown()
        del self.pluginConfig[pluginName]
        del self.botPlugin[pluginName]

    def registerBotPlugin(self, pluginname, config):
        """ Registers a bot plugin pluginname is the file and class name,
        and config is an xml element passed to the plugin. Will reload the plugin module,
        so previously loaded plugins can be updated.
        """
        if pluginname in globals()['plugins'].__dict__:
            reload(globals()['plugins'].__dict__[pluginname])
        else:
            __import__(self.plugin_name_to_module(pluginname))
        self.botPlugin[pluginname] = getattr(globals()['plugins'].__dict__[pluginname], pluginname)(self, config)
        self.pluginConfig[pluginname] = config
        return True

    def message_from_owner(self, msg):
        """ Was this message sent from a bot owner?
        """
        jid = self.get_real_jid(msg)
        return jid in self.owners

    def message_from_admin(self, msg):
        """ Was this message sent from a bot admin?
        """
        jid = self.get_real_jid(msg)
        return jid in self.admins

    def message_from_member(self, msg):
        """ Was this message sent from a bot member?
        """
        jid = self.get_real_jid(msg)
        return jid in self.members

    def getMemberClassJids(self, userClass):
        """ Returns a list of all jids belonging to users of a given class
        """
        jids = []
        users = self.botconfig.findall('users/' + userClass)
        if users:
            for user in users:
                userJids = user.findall('jid')
                if userJids:
                    for jid in userJids:
                        logging.debug("appending %s to %s list" % (jid.text, userClass))
                        jids.append(jid.text)
        return jids

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

    def should_answer_message(self, msg):
        """ Checks whether the bot is configured to respond to the sender of a message.
        """
        return self.shouldAnswerToJid(self.get_real_jid(msg))

    def shouldAnswerToJid(self, jid):
        """ Checks whether the bot is configured to respond to the specified jid.
            Pass in a muc jid if you want, it'll be converted to a real jid if possible
            Accepts 'None' jids (acts as an unknown user).
        """
        if jid in self.banned:
            return False
        if not self.botconfig.find('require-membership'):
            return True
        if jid in self.members or jid in self.admins or jid in self.owners:
            return True
        return False

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
        logging.info("Deregistering bot plugins for rehash")
        del globals()['plugins']
        globals()['plugins'] = __import__('plugins')
        self.reset_bot()
        self.deregister_bot_plugins()
        logging.info("Reloading config file")
        self.botconfig = self.loadConfig(self.configFile)
        self.register_bot_plugins()
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
        self.deregister_bot_plugins()
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
