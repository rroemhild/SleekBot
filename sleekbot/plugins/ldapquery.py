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
    """ Dict for an LDAP entry.
    """

    def __init__(self, entry):
        dict.__init__(self)
        for key in entry.keys():
            self[key] = entry[key][0].decode('utf-8')


class Queries():
    """ A dirty hack to set the plugin command usage after the plugin
        was registerd with the bot.
    """

    def __init__(self):
        self.value = ''

    def __str__(self):
        return self.value

QUERIES = Queries()


class QueryObject():
    """ Object to perform each LDAPQuery
    """

    def __init__(self, config):
        self.config = config
        self.name = config.get('name')
        self.help = config.get('help')
        self.usage = config.get('usage')
        self.order = config.get('order', '')
        self.response = config.get('response')
        self.delimiter = config.get('delimiter', ',')
        self.retrieve_attrib = config.get('retvattrs', '').split(',')
        srv = config.get('server')
        self.server = {
            'uri': srv.get('uri', 'ldap://localhost:389/'),
            'binddn': srv.get('binddn', ''),
            'secret': srv.get('secret', ''),
            'basedn': srv.get('basedn', ''),
            'timeout': srv.get('timeout', 10),
            'search_scope': ldap.SCOPE_SUBTREE,
        }

    def __unicode__(self):
        return self.name

    def get_help(self):
        """ Returns the LDAPQuery command help
        """

        return "ldap %s -- %s\nUsage: %s\n" % (self.name, self.help, self.usage)

    def run(self, query):
        """ Make the searchfilter, perform the search and return the result
        """

        query = ldap.filter.escape_filter_chars(query)
        search_filter = self.config.get('filter').replace('%s', query)
        logging.debug('LDAP search filter: %s', search_filter)
        results = self.ldap_search(search_filter)
        logging.debug('LDAP search results: %s', results)

        response = []
        entries = []
        if results:
            for result in results:
                entries.append(LdapEntry(result[1]))
            if self.order == 'sorted':
                entries.sort()
        limit = self.config.get('limit', len(entries))
        for entry in entries[:limit]:
            response.append(self.response % entry)

        if len(response) > 0:
            return "%s" % self.delimiter.join(response)
        else:
            return "No search result."

    def ldap_search(self, search_filter):
        """ Run a search on LDAP server
        """

        logging.debug('Connecting to ldap server %s', self.server['uri'])
        _ldap = ldap.initialize(self.server['uri'])
        try:
            _ldap.simple_bind_s(self.server['binddn'], self.server['secret'])
            logging.debug('Connected to ldap server.')
        except ldap.LDAPError as error:
            logging.error('LDAP %s', error)

        try:
            result_set = _ldap.search_st(self.server['basedn'],
                                            self.server['search_scope'],
                                            search_filter, self.retrieve_attrib,
                                            0, self.server['timeout'])
            _ldap.unbind_s()
            logging.debug('Disconnected from LDAP server.')
            return result_set
        except ldap.LDAPError as error:
            logging.error('LDAP %s', error)

class LDAPQuery(BotPlugin):
    """ Ldapbot allows users to query LDAP servers.
    """

    def __init__(self, queries=()):
        BotPlugin.__init__(self)
        self._queries = queries
        self.global_queries = {}

    def _on_register(self):
        """ Build the botcmd usage bevor the command gets
            registered with the commandbot. 
        """

        for query in self._queries:
            logging.debug("Load ldap-query: %s", query['name'])
            self.global_queries[query['name']] = QueryObject(query)

        global QUERIES
        QUERIES.value = '[%s]' % '|'.join(self.global_queries)

    def example_config(self):
        """ Configuration example.
        """

        return {'queries':
                ({'name': 'user',
                'help': 'Return some user info',
                'usage': 'user [givenname|surname]',
                'server': {'uri': 'ldap://localhost:389',
                           'binddn': 'cn=admin,dc=server,dc=com',
                           'secret': 'mySecret',
                           'basedn': 'ou=people,dc=server,dc=com',
                           'timeout': 10},
                'filter': '(&(objectClass=*)(|(sn=*%s*)(givenName=*%s*)))',
                'delimiter': '\\n',
                'limit': 1,
                'retvattrs': 'sn,givenName,mail',
                'response': '%(givenName)s %(sn)s\nE-Mail: %(mail)s',
                'order': 'sorted'})}

    @botcmd(name='ldap', usage=QUERIES)
    def handle_ldapquery(self, command, args, msg):
        """ Achieve a query on a LDAP Server.
        """

        search = None
        query = args.split(' ', 1)[0]
        if ' ' in args:
            search = args.split(' ', 1)[-1]
        if query in self.global_queries:
            query = self.global_queries[query]
            if not search:
                return query.get_help()
            return query.run(search)
        return "Unknown option."

