"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

import time
import math
import logging
from urllib import urlopen
from xml.etree import ElementTree as ET

from sleekbot.plugbot import BotPlugin
from sleekbot.commandbot import botcmd
from sleekbot.commandbot import parse_args, ArgError

class XEPinfo(BotPlugin):
    """A plugin for obtaining xep information."""
    
    RESPONSE_INFO = '%(type)s XEP-%(number)s, %(name)s, is %(status)s ' \
                   '(last updated %(updated)s): ' \
                   'http://www.xmpp.org/extensions/xep-%(number)s.html'

    RESPONSE_TOOMANY = '\n\n%(number)s more results were found but not shown ' \
                       '(too many results).'
                      
    RESPONSE_ERROR = 'I have suffered a tremendous error: I cannot reach the ' \
                     'XEP list (and have never been able to)'
                     
    RESPONSE_NOTFOUND = 'The XEP you specified ("%s") could not be found'
    
    def __init__(self, *args, **kwargs):
        super(XEPinfo, self).__init__(*args, **kwargs)
        self._last_cache_time = 0
        self._xeps = None    
                     
    def _on_register(self):
        """ Loads XEP cache if necessary """
        self._ensure_cache_is_recent()

    def _ensure_cache_is_recent(self):
        """ Check if the xep list cache is older than the age limit in config 
            and refreshes if so.
        """
        now = math.floor(time.time())
        expiry_seconds = int(self.config.find('cache').attrib['expiry']) * 3600
        if self._last_cache_time + expiry_seconds < now:
            self._refresh_cache()

    def _refresh_cache(self):
        """ Updates the xep list cache.
        """
        url = self.config.find('xeps').attrib['url']
        try:
            url_object = urlopen(url)
            self._xeps = ET.parse(url_object).getroot()
            self._last_cache_time = math.floor(time.time())
        except IOError as ex:
            logging.info('Getting XEP list file %s failed. %s', url, ex)

    @botcmd(name='xep', usage='[number]')
    def handle_xep(self, command, args, msg):
        """Returns details of the specified XEP."""
        self._ensure_cache_is_recent()
        
        try:
            args = parse_args(args, (('xep', int), ))
        except ArgError as ex:
            return ex.msg

        xepnumber = '%04i' % int(args.xep)

        if self.xeps == None:
            return self.RESPONSE_ERROR
            
        response = ''
        num_responses = 0
        for xep in self._xeps.findall('xep'):
            if xep.find('number').text == xepnumber or \
               xep.find('name').text.lower().find(args.lower()) >= 0:
                num_responses = num_responses + 1
                if num_responses > 6:
                    continue
                if response != '':
                    response = response + "\n\n"
                response = response + self.RESPONSE_INFO
                texts = {}
                for prop in ('type', 'number', 'name', 'status', 'updated'):
                    texts[prop] = xep.find(prop).text
                response = response % texts

        if num_responses > 6:
            response = response + self.RESPONSE_TOOMANY
            num_response_key = {}
            num_response_key['number'] = num_responses - 6
            response = response % num_response_key

        if response == '':
            response = self.RESPONSE_NOTFOUND % args

        return response
