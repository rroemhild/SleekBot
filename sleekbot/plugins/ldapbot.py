"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

""" Configuration example
<plugin name="ldapbot">
    <config>
        <server uri="ldap://server.com:389" binddn="" secret="" />
        <option name="user" help="Returns some user info" usage="user [givenname|surname|uid]">
            <basedn dn="ou=people,dc=domain,dc=tld" />
            <searchFilter>(&amp;(account=active)(|(uid=*%s*)(sn=*%s*)(givenName=*%s*)(displayName=*%s*)))</searchFilter>
            <retrieveAttributes>
                <attr name="sn" />
                <attr name="givenName" />
                <attr name="mail" />
                <attr name="ou" />
                <attr name="telephoneNumber" />
            </retrieveAttributes>
            <response msg="%(givenName)s %(sn)s\nOrg: %(ou)s\nE-Mail: %(mail)s\nPhone: %(telephoneNumber)s" order="sorted" delimiter="\n" limit="1" />
        </option>
    </config>
</plugin>
"""

import logging

import ldap
import ldap.filter

from sleekbot.commandbot import botcmd
from sleekbot.plugbot import BotPlugin


class LdapEntry(dict):
    """Dict for an LDAP entry"""
    def __init__(self, entrie):
        for key in entrie.keys():
            self[key] = entrie[key][0].decode('utf-8')


class Options():
    """A dirty hack to set the plugin command usage after the plugin
    was registerd with the bot.
    """
    def __init__(self):
        self.x = ''

    def __str__(self):
        return self.x

options = Options()


class ldapbot(BotPlugin):
    """Ldapbot allows users to query a LDAP server.
    """

    def on_register(self):
        self.ldap = None
        self.plugin_options = {}

        for option in self.config.findall('option'):
            self.plugin_options[option.attrib['name']] = {
                'name': option.attrib['name'],
                'help': option.attrib['help'],
                'usage': option.attrib['usage'],
                'basedn': option.find('basedn').attrib['dn'],
                'order': option.find('response').get('order', default='sorted'),
                'limit': option.find('response').get('limit'),
                'delimiter': option.find('response').get('delimiter', default=", ").replace('\\n', '\n'),
                'responseMsg': option.find('response').get('msg', default='').replace('\\n', '\n'),
                'searchFilter': option.find('searchFilter').text,
                'retrieveAttributes': option.find('retrieveAttributes')}

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
        """ Return a integer for the output limit of entries
        """
        if not limit:
            limit = default
        elif not limit.isdigit():
            limit = default
        return int(limit)

    def ldap_search(self, searchFilter, retrieveAttrib, option):
        """ Run a search on LDAP server
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
            logging.debug('Disconnected from LDAP server.')
            return result_set
        except ldap.LDAPError as e:
            logging.error('LDAP %s' % e)

    @botcmd(name='ldap', usage=options)  # options is global
    def handle_ldapsearch(self, command, args, msg):
        """ Achieve a query on a LDAP Server."""

        opt = ''
        query = ''

        opt = args.split(' ', 1)[0]
        if ' ' in args:
            query = ldap.filter.escape_filter_chars(args.split(' ', 1)[-1])

        responseTemp = []

        if opt in self.plugin_options:
            option = self.plugin_options[opt]

            # Returns plugin command help if there is no query
            if query == '':
                return "ldap %s -- %s\nUsage: %s\n" % (opt,
                                                        option['help'],
                                                        option['usage'])

            searchFilter = ''
            searchFilter = option['searchFilter'].replace('%s', query)
            logging.debug('LDAP search filter: %s' % searchFilter)

            # responseable message attributes
            retrieveAttributes = []
            for sr in option['retrieveAttributes'].findall('attr'):
                retrieveAttributes.append(sr.attrib['name'])

            # ldap search
            results = self.ldap_search(searchFilter, retrieveAttributes, option)
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
                return "No search result."

        return "Unknown option."
