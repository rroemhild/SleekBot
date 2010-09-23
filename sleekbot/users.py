"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

import logging

def parts_of(address):
    yield address
    if '@' in address:
        (pre, dom) = address.split('@', 1)
        yield dom
        while '.' in dom:
            (pre, dom) = dom.split(".", 1)
            yield dom

class eset(set):
    """A set class for e-mail addresses that can checks membership based on domains"""

    def __contains__(self, item):
        for p in parts_of(item):
            if super(eset, self).__contains__(p):
                return True
        return False

def get_jids_in_group(xmlnode, group):
    """ Returns a list of all jids belonging to users of a given group
    """
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

class Users(object):

    def __init__(self, config = dict()):
        self.owners = eset()
        self.admins = eset()
        self.members = eset()
        self.banned = eset()

    def update_from_xml(self, xmlnodes):
        for xmlnode in xmlnodes:
            self.owners.update(get_jids_in_group(xmlnode, 'owner'))
            self.admins.update(get_jids_in_group(xmlnode, 'admin'))
            self.members.update(get_jids_in_group(xmlnode, 'member'))
            self.banned.update(get_jids_in_group(xmlnode, 'banned'))



if __name__ == '__main__':
    a = eset(['test@a.new.domain.com'])
    b = eset(['a.new.domain.com'])
    c = eset(['domain.com'])
    xs = ['test@a.new.domain.com', 'test2@a.new.domain.com', 'test3@another.domain.com', 'test4@domain.us', 'us']
    for s in [a, b, c]:
        print("---> ", s)
        for x in xs:
            print('%s: %s' % (x, x in s))