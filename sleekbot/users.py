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



# Possible groups for users
GROUP = Enum(['undefined', 'banned', 'member', 'admin', 'owner'])

class Users(object):
    """ Non-persistent storage for users and groups.
    """

    def __init__(self, config = dict()):
        self.__dict = defaultdict(str)

        # Provide syntactic sugar for accesing the groups within Users
        self.banned = virtual_set(self, GROUP.banned)
        self.admins = virtual_set(self, GROUP.admin)
        self.owners = virtual_set(self, GROUP.owner)
        self.members = virtual_set(self, GROUP.member)


    def update_from_xml(self, xmlnode):
        """ Add the jids in an xmlnode.
        """

        for group in GROUP:
            for jid in get_jids_in_group(xmlnode, group):
                self.__dict[jid] = getattr(GROUP, group)

    def check(self, jid, group):
        """ Check if jid is in a group/groups.
                jid   -- a string with the jid or domain to check
                group -- an item of GROUP enum or collection of such items
        """

        if not isinstance(group, collections.Iterable):
            group = [group]
        for p in parts_of(jid):
            if self.__dict[p] in group:
                return True
        return False

    def count(self, group):
        """ Returns the number of jids that are in group.
        """
        return self.__dict.values().count(group)


if __name__ == '__main__':
    a = eset(['test@a.new.domain.com'])
    b = eset(['a.new.domain.com'])
    c = eset(['domain.com'])
    xs = ['test@a.new.domain.com', 'test2@a.new.domain.com', 'test3@another.domain.com', 'test4@domain.us', 'us']
    for s in [a, b, c]:
        print("---> ", s)
        for x in xs:
            print('%s: %s' % (x, x in s))