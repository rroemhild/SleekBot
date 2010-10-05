"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

import logging
from collections import defaultdict

try:
    import ldap
    import ldap.filter
except:
    logging.error("can not import ldap. LDAP storage for acl" \
                    " is not available.")


def parts_of(address):
    """ Given an e-mail address, generates al possible domains."""
    yield address
    if '@' in address:
        dom = address.split('@', 1)[-1]
        yield dom
        while '.' in dom:
            dom = dom.split(".", 1)[-1]
            yield dom


def in_clause_subs(number):
    """ Returns a string with n question marks to be used as substitutions
    placeholders in sql queries.
    """
    return ','.join(['?'] * number)


def get_jids_in_group(xmlnode, group):
    """ Returns a list of all jids belonging to users of a given group."""
    jids = []
    users = xmlnode.findall(group)
    if not users:
        return jids
    for user in users:
        user_jids = user.findall('jid')
        if user_jids:
            for jid in user_jids:
                logging.debug("appending %s to %s list", jid.text, group)
                jids.append(jid.text)
    return jids


class ESet(set):
    """A set class for e-mail addresses that checks
    membership based on domains.
    """

    def __contains__(self, item):
        for part in parts_of(item):
            if super(ESet, self).__contains__(part):
                return True
        return False


class LdapEntry(dict):
    """ Dict for an LDAP entry."""
    def __init__(self, entrie):
        for key in entrie.keys():
            self[key] = entrie[key][0].decode('utf-8')


class VirtualSet(object):
    """ A ennumerable object to access the keys
    of a value-filtered key-value dictionary.
    """

    def __init__(self, users, prop):
        self.__prop = prop
        self.__users = users

    def __len__(self):
        return self.__users.count(self.__prop)

    def __contains__(self, item):
        return self.__users.check(item, self.__prop)


class Enum(list):
    """ A simple enum class."""

    def __init__(self, names):
        super(Enum, self).__init__(names)
        for value, name in enumerate(names):
            setattr(self, name, value)

    def tuples(self):
        """ Returns a tuple of enumerated names."""
        return tuple(enumerate(self))


class ACL(object):
    """ Non-persistent storage for access control lists
    """

    ROLE = Enum(['undefined', 'banned', 'user', 'admin', 'owner'])

    def __init__(self, caller, config=None):
        self.__dict = defaultdict(str)
        self._post_init()

    def _post_init(self):
        """ Provide syntactic sugar for accesing the different roles."""
        self.banned = VirtualSet(self, ACL.ROLE.banned)
        self.admins = VirtualSet(self, ACL.ROLE.admin)
        self.owners = VirtualSet(self, ACL.ROLE.owner)
        self.users = VirtualSet(self, ACL.ROLE.user)

    def __getitem__(self, jid):
        return self.__dict[jid]

    def __setitem__(self, jid, role):
        self.__dict[jid] = role

    def __delitem__(self, jid):
        del self.__dict[jid]

    def __contains__(self, jid):
        return jid in self.__dict

    def update_from_xml(self, xmlnode):
        """ Add the jids in an xmlnode.
        """

        for role in ACL.ROLE:
            for jid in get_jids_in_group(xmlnode, role):
                self[jid] = getattr(ACL.ROLE, role)

    def find_part(self, jid):
        """ For a given jid, find the part that is in the acl
        """
        for part in parts_of(jid):
            if part in self:
                return part
        return None

    def check(self, jid, role):
        """ Check if jid is in a role/roles
                jid  -- a string with the jid or domain to check
                role -- an item of ROLE enum or collection of such items
        """

        if not isinstance(role, (list, tuple)):
            role = (role, )
        for part in parts_of(jid):
            if self[part] in role:
                return True
        return False

    def count(self, role=None):
        """ Returns the number of jids that are in role/roles
        """
        if role is None:
            return len(self)

        if isinstance(role, (list, tuple)):
            return reduce(sum, [self.__dict.values().count(r) for r in role])

        return self.__dict.values().count(role)

    def summarize(self):
        """ Sumarizes the number of users per role in a string
        """
        summary = ['%d %s' % (self.count(getattr(self.ROLE, role)), role)
                    for role in ACL.ROLE]
        return ', '.join(summary) + '.'


class ACLdb(ACL):
    """ Database storage for access control lists
    """

    def __init__(self, caller, config=None):
        self.store = caller.store
        self.create_table()
        self._post_init()

    def create_table(self):
        """ Creates the sql table to hold the users if needed."""
        with self.store.context_cursor() as cur:
            if not len(cur.execute("pragma table_info('acl')").fetchall()) > 0:
                cur.execute('CREATE TABLE "acl" ("id" INTEGER PRIMARY KEY ' \
                   'AUTOINCREMENT, "jid" VARCHAR(256) UNIQUE, "role" INTEGER)')
                cur.execute('CREATE INDEX idx_role ON acl (role)')
                logging.info("ACLdb: acl table created")

    def __getitem__(self, jid):
        with self.store.context_cursor() as cur:
            cur.execute('SELECT role FROM acl WHERE jid = ?', (jid, ))
            return cur.fetchone()[0]

    def __setitem__(self, jid, role):
        with self.store.context_cursor() as cur:
            cur.execute('SELECT * FROM acl WHERE jid=?', (jid, ))
            if (len(cur.fetchall()) > 0):
                cur.execute('UPDATE acl SET jid=?, role=? WHERE jid=?',
                            (jid, role, jid))
            else:
                cur.execute('INSERT INTO acl(jid, role) VALUES(?,?)',
                            (jid, role))

    def __delitem__(self, jid):
        with self.store.context_cursor() as cur:
            cur.execute('DELETE FROM acl WHERE jid=?', (jid, ))

    def __contains__(self, jid):
        with self.store.context_cursor() as cur:
            cur.execute('SELECT count(*) FROM acl WHERE jid = ?', (jid, ))
            return int(cur.fetchone()[0]) > 0

    def check(self, jid, role):
        """ Check if jid is in a role/roles
                jid  -- a string with the jid or domain to check
                role -- an item of ROLE enum or collection of such items
        """
        jid = tuple(parts_of(jid))
        if isinstance(role, (list, tuple)):
            query = 'SELECT count(*) FROM acl ' \
                    'WHERE jid IN (%s) and role IN (%s)' \
                    % (in_clause_subs(len(jid)), in_clause_subs(len(role)))
            pars = jid + tuple(role)
        else:
            query = 'SELECT count(*) FROM acl WHERE jid IN (%s) and role = ?' \
                    % (in_clause_subs(len(jid)))
            pars = jid + (role, )

        with self.store.context_cursor() as cur:
            cur.execute(query, pars)
            return int(cur.fetchone()[0]) > 0

    def count(self, role=None):
        """ Returns the number of jids that are in role.
        """
        if role is None:
            query = 'SELECT count(*) FROM acl'
            role = ()
        elif isinstance(role, (list, tuple)):
            query = 'SELECT count(*) FROM acl WHERE role IN (%s)' \
                    % in_clause_subs(role)
        else:
            query = 'SELECT count(*) FROM acl WHERE role = ?'
            role = (role, )

        with self.store.context_cursor() as cur:
            cur.execute(query, role)
            return int(cur.fetchone()[0])


class ACLldap(ACL):
    """ LDAP storage for access control lists
    """

    def __init__(self, caller, config=None):
        self._post_init()
        self.config = config
        self.caller = caller
        self.searchScope = ldap.SCOPE_SUBTREE
        self.ldap = self._bind()

    def _bind(self):
        """Connect to the LDAP Server"""

        l = ldap.initialize(self.config.find('server').get('uri'))
        l.timeout = 10

        try:
            l.simple_bind_s(self.config.find('server').get('binddn'),
                            self.config.find('server').get('secret'))
        except ldap.INVALID_CREDENTIALS:
            logging.error("LDAP username or password is incorrect.")
            return False
        except ldap.SERVER_DOWN:
            logging.error("LDAP server %s down" % self.uri)
            return False
        except ldap.LDAPError, e:
            logging.error('LDAP %s' % e)
            return False

        logging.info('Bind to LDAP Server %s' \
            % self.config.find('server').get('uri'))
        return l

    def __getitem__(self, jid):
        if self.ldap:
            searchFilter = "(&(objectClass=%s)(memberUid=%s))" \
                % (self.config.find('groups').get('groupClass', '*'),
                jid)
            retrieveAttrib = ['cn']
            result_set = self.ldap.search_st(
                    self.config.find('groups').get('basedn'),
                    self.searchScope, searchFilter, retrieveAttrib, 0,
                    int(self.config.find('server').get('timeout', 10)))
            entry = LdapEntry(result_set[0][1])
            return getattr(self.caller.acl.ROLE, entry['cn'])

    def __contains__(self, jid):
        if self.ldap:
            searchFilter = "(&(objectClass=%s)(%s=%s))" \
                % (self.config.find('groups').get('groupclass', '*'),
                    self.config.find('groups').get('memberattr', '*'),
                    jid)
            retrieveAttrib = ['cn']
            result_set = self.ldap.search_st(
                    self.config.find('groups').get('basedn'),
                    self.searchScope, searchFilter, retrieveAttrib, 0,
                    int(self.config.find('server').get('timeout', 10)))
            return len(result_set) > 0


if __name__ == '__main__':
    a = eset(['test@a.new.domain.com'])
    b = eset(['a.new.domain.com'])
    c = eset(['domain.com'])
    xs = ['test@a.new.domain.com', 'test2@a.new.domain.com', \
         'test3@another.domain.com', 'test4@domain.us', 'us']
    for s in [a, b, c]:
        print("---> ", s)
        for x in xs:
            print('%s: %s' % (x, x in s))
