"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

import logging

import ldap
import ldap.filter

from sleekbot.commandbot import botcmd
from sleekbot.plugbot import BotPlugin

class LdapEntry(dict):
    """ Dict for an LDAP entry """
    def __init__(self, entrie):
        for key in entrie.keys():
            self[key] = entrie[key][0].decode('utf-8')

class Options():
    def __init__(self):
        self.x = ''
        
    def __str__(self):
        return self.x
        
options = Options()

class ldapbot(BotPlugin):
    """Ldapbot allows users to query an LDAP server.
    Written By: Rafael Roemhild"""
       
    def on_register(self):
        self.ldap = None
        self.plugin_options = {}
        
        for option in self.config.findall('option'):
            self.plugin_options[option.attrib['name']] = {
                'name' : option.attrib['name'],
                'basedn' : option.find('basedn').attrib['dn'],
                'order' : option.find('response').get('order', default='sorted'),
                'limit' : option.find('response').get('limit'),
                'delimiter' : option.find('response').get('delimiter', default=", ").replace('\\n', '\n'),
                'responseMsg' : option.find('response').get('msg', default='').replace('\\n', '\n'),
                'searchFilterAttrib' : option.find('filter').findall('attr'),
                'searchRequireAttrib' : option.find('require').findall('attr'),
                'searchReturnAttrib' : option.find('return').findall('attr')}
        
        global options
        options.x = '[%s]' % '|'.join(self.plugin_options)
    
    def get_available_commands(self, options):
        """ Return a list with search commands
        """
        temp = []
        for option in options:
            temp.append(option.attrib['name'])
        return temp
    
    def get_entries_limit(self, limit, default=1):
        """ Return an ineger for the output limit on entries
        """
        if not limit:
            limit = default
        elif not limit.isdigit():
            limit = default
        return int(limit)
    
    def merge_search_filter(self, option, query):
        """ Merge ldap search filter from config
        """
        # merge the OR search part
        filters = []
        for sf in option['searchFilterAttrib']:
            ldap_attrib = sf.attrib['name']
            search_value = sf.get("value", default="%(query)s") % {'query': ldap.filter.escape_filter_chars(query)}
            if sf.get('exclude', default="") == "!":
                ldap_attrib = "!%s" % ldap_attrib
            filters.append('(%s=%s)' % (ldap_attrib, search_value))
        
        # merge the AND search part
        requires = []
        for sr in option['searchRequireAttrib']:
            ldap_attrib = sr.attrib['name']
            if sr.get('exclude', default="") == "!":
                ldap_attrib = "!%s" % ldap_attrib
            requires.append('(%s=%s)' % (ldap_attrib, sr.get('value', default="*")))
        
        # merge both lists to one search filter
        return '(&' + ' '.join(requires) + '(|' + ' '.join(filters) +'))'
    
    def ldap_search(self, searchFilter, retrieveAttrib, option):
        """ Run a search on ldap server
        """
        logging.debug('Connecting to ldap server %s' % self.config.find('server').attrib['uri'])
        self.ldap = ldap.initialize(self.config.find('server').attrib['uri'])
        try:
            self.ldap.simple_bind_s(self.config.find('server').get('binddn'),
                                    self.config.find('server').get('secret'))
            logging.debug('Connected to ldap server.')
        except ldap.LDAPError as e:
            logging.error('LDAP %s' % e)
        
        searchScope = ldap.SCOPE_SUBTREE
        try:
            result_set = self.ldap.search_st(option['basedn'], searchScope,
                                            searchFilter, retrieveAttrib, 0,
                                            int(self.config.find('server').get('timeout', 10)))
            self.ldap.unbind_s()
            logging.debug('Diconnected from LDAP server.')
            return result_set
        except ldap.LDAPError as e:
            logging.error('LDAP %s' % e)
    
    @botcmd(name = 'ldap', usage = options)
    def handle_ldapsearch(self, command, args, msg):
        """Query an LDAP Server"""
        opt = args.split(' ', 1)[0]
        query = ''
        if ' ' in args:
            query = args.split(' ', 1)[-1]
        else:
            return "No query."
        responseTemp = []
        
        if opt in self.plugin_options:
            option = self.plugin_options[opt]
            searchFilter = self.merge_search_filter(option, query)
            logging.debug('LDAP search filter: %s' % searchFilter)
            
            # responseable message attributes
            retrieveAttrib = []
            for sr in option['searchReturnAttrib']:
                retrieveAttrib.append(sr.attrib['name'])
            
            # ldap search
            results = self.ldap_search(searchFilter, retrieveAttrib, option)
            logging.debug('LDAP search results: %s' % results)

            # response
            entries = []
            if results:
                for e in results:
                    entries.append(LdapEntry(e[1]))
                if option['order'] == 'sorted':
                    entries.sort()
            limit = self.get_entries_limit(option['limit'], len(entries))
            for entry in entries[:limit]:
                responseTemp.append(option['responseMsg'] % entry)

            if len(responseTemp) > 0:
                return "%s" % option['delimiter'].join(responseTemp)
            else:
                return "No search results."
        
        return "No such option: %s" % opt
