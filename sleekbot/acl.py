"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

import logging

import collections
from collections import defaultdict

def parts_of(address):
    """ Given an e-mail address, generates al possible domains."""
    yield address
    if '@' in address:
        (pre, dom) = address.split('@', 1)
        yield dom
        while '.' in dom:
            (pre, dom) = dom.split(".", 1)
            yield dom

def in_clause_subs(n):
    return ','.join(['?']*n)

def get_jids_in_group(xmlnode, group):
    """ Returns a list of all jids belonging to users of a given group."""
    jids = []
    users = xmlnode.findall(group)
    if users:
        for user in users:
            userJids = user.findall('jid')
            if userJids:
                for jid in userJids:
                    logging.debug("appending %s to %s list" % (jid.text, group))
                    jids.append(jid.text)
    return jids


class eset(set):
    """A set class for e-mail addresses that checks membership based on domains."""

    def __contains__(self, item):
        for p in parts_of(item):
            if super(eset, self).__contains__(p):
                return True
        return False


class virtual_set(object):
    """ A ennumerable object to access the keys of a value-filtered key-value dictionary.
    """

    def __init__(self, users, prop):
        self.__prop = prop
        self.__users = users

    def __len__(self):
        return self.__users.count(self.__prop)

    def __contains__(self, item):
        return self.__users.check(item, self.__prop)


class Enum(set):
    """ A simple enum class."""

    def __init__(self, names):
        super(Enum, self).__init__(names)
        for value, name in enumerate(names):
            setattr(self, name, value)

    def tuples(self):
        return tuple(enumerate(self))


class ACL(object):
    """ Non-persistent storage for access control lists
    """

    ROLE = Enum(['undefined', 'banned', 'user', 'admin', 'owner'])

    def __init__(self, caller, config = None):
        self.__dict = defaultdict(str)
        self._post_init()


    def _post_init(self):
        """ Provide syntactic sugar for accesing the different roles."""
        self.banned = virtual_set(self, ACL.ROLE.banned)
        self.admins = virtual_set(self, ACL.ROLE.admin)
        self.owners = virtual_set(self, ACL.ROLE.owner)
        self.users = virtual_set(self, ACL.ROLE.user)


    def update_from_xml(self, xmlnode):
        """ Add the jids in an xmlnode.
        """

        for role in ACL.ROLE:
            for jid in get_jids_in_group(xmlnode, role):
                self.__dict[jid] = getattr(ACL.ROLE, role)


    def check(self, jid, role):
        """ Check if jid is in a role/roles
                jid  -- a string with the jid or domain to check
                role -- an item of ROLE enum or collection of such items
        """

        if not isinstance(role, collections.Iterable):
            role = (role, )
        for p in parts_of(jid):
            if self.__dict[p] in role:
                return True
        return False


    def count(self, role):
        """ Returns the number of jids that are in role/roles
        """
        if isinstance(role, collections.Iterable):
            return reduce(sum, [self.__dict.values().count(r) for r in role])

        return self.__dict.values().count(role)


class ACLdb(ACL):
    """ Database storage for access control lists
    """

    def __init__(self, caller, config = None):
        self.store = caller.store
        self.create_table()
        self._post_init()


    def create_table(self):
        db = self.store.getDb()
        if not len(db.execute("pragma table_info('acl')").fetchall()) > 0:
            db.execute('CREATE TABLE "acl" ("id" INTEGER PRIMARY KEY AUTOINCREMENT, "jid" VARCHAR(256) UNIQUE, "role" INTEGER)')
            db.execute('CREATE INDEX idx_role ON acl (role)')
            logging.info("ACLdb: acl table created")
        db.close()


    def update_from_xml(self, xmlnode):
        """ Add the jids in an xmlnode.
        """

        for role in ACL.ROLE:
            for jid in get_jids_in_group(xmlnode, role):
                self.update(jid, getattr(ACL.ROLE, role))


    def check(self, jid, role):
        """ Check if jid is in a role/roles
                jid  -- a string with the jid or domain to check
                role -- an item of ROLE enum or collection of such items
        """
        jid = tuple(parts_of(jid))
        if isinstance(role, collections.Iterable):
            query = 'SELECT count(*) FROM acl WHERE jid IN (%s) and role IN (%s)' % (in_clause_subs(len(jid)), in_clause_subs(len(role)))
            pars = jid + tuple(role)
        else:
            query = 'SELECT count(*) FROM acl WHERE jid IN (%s) and role = ?' % (in_clause_subs(len(jid)))
            pars = jid + (role, )

        db = self.store.getDb()
        cur = db.cursor()
        cur.execute(query, pars)
        ans = int(cur.fetchone()[0]) > 0
        db.close()
        return ans


    def count(self, role):
        """ Returns the number of jids that are in role.
        """
        if isinstance(role, collections.Iterable):
            query = 'SELECT count(*) FROM acl WHERE role IN (%s)' % in_clause_subs(role)
        else:
            query = 'SELECT count(*) FROM acl WHERE role = ?'
            role = (role, )

        db = self.store.getDb()
        cur = db.cursor()
        cur.execute(query, role)
        ans = int(cur.fetchone()[0])
        db.close()
        return ans


    def update(self, jid, role):
        db = self.store.getDb()
        cur = db.cursor()
        cur.execute('SELECT * FROM acl WHERE jid=?', (jid, ))
        if (len(cur.fetchall()) > 0):
            cur.execute('UPDATE acl SET jid=?, role=? WHERE jid=?', (jid, role, jid))
        else:
            cur.execute('INSERT INTO acl(jid, role) VALUES(?,?)', (jid, role))
        db.commit()
        db.close()



if __name__ == '__main__':
    a = eset(['test@a.new.domain.com'])
    b = eset(['a.new.domain.com'])
    c = eset(['domain.com'])
    xs = ['test@a.new.domain.com', 'test2@a.new.domain.com', 'test3@another.domain.com', 'test4@domain.us', 'us']
    for s in [a, b, c]:
        print("---> ", s)
        for x in xs:
            print('%s: %s' % (x, x in s))