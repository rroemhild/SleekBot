"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

import logging
from urllib import urlopen
from xml.etree import ElementTree as ET
import time
import math

from sleekbot.commandbot import botcmd
from sleekbot.plugbot import BotPlugin

class xepbot(BotPlugin):
    """A plugin for obtaining xep information."""

    def on_register(self):
        self.lastCacheTime = 0
        self.xeps = None
        self.ensureCacheIsRecent()

    def ensureCacheIsRecent(self):
        """ Check if the xep list cache is older than the age limit in config and refreshes if so.
        """
        now = math.floor(time.time())
        expirySeconds = int(self.config.find('cache').attrib['expiry']) * 60 * 60
        if self.lastCacheTime + expirySeconds < now:
            self.refreshCache()

    def refreshCache(self):
        """ Updates the xep list cache.
        """
        url = self.config.find('xeps').attrib['url']
        try:
            urlObject = urlopen(url)
            self.xeps = ET.parse(urlObject).getroot()
            self.lastCacheTime = math.floor(time.time())
        except:
            logging.info("Loading XEP list file %s failed." % (url))

    @botcmd(name = 'xep', usage = '[number]')
    def handle_xep(self, command, args, msg):
        """Returns details of the specified XEP."""
        self.ensureCacheIsRecent()
        if args == None or args == "":
            return "Please supply a xep number or a search term"
        try:
            xepnumber = '%04i' % int(args)
        except:
            xepnumber = ''
        if self.xeps == None:
            return 'I have suffered a tremendous error: I cannot reach the XEP list (and have never been able to)'
        response = ''
        numResponses = 0
        for xep in self.xeps.findall('xep'):
            if xep.find('number').text == xepnumber or xep.find('name').text.lower().find(args.lower()) >= 0:
                numResponses = numResponses + 1
                if numResponses > 6:
                    continue
                if response != '':
                    response = response + "\n\n"
                response = response + '%(type)s XEP-%(number)s, %(name)s, is %(status)s (last updated %(updated)s): http://www.xmpp.org/extensions/xep-%(number)s.html'
                texts = {}
                texts['type'] = xep.find('type').text
                texts['number'] = xep.find('number').text
                texts['name'] = xep.find('name').text
                texts['status'] = xep.find('status').text
                texts['updated'] = xep.find('updated').text
                response = response % texts
        if numResponses > 6:
            response = response + '\n\n%(number)s more results were found but not shown (too many results).'
            numResponseKey = {}
            numResponseKey['number'] = numResponses - 6
            response = response % numResponseKey
        if response == '':
            response = 'The XEP you specified ("%s") could not be found' % args
        return response
