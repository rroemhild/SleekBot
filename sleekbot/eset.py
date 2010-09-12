"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

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

if __name__ == '__main__':
    a = eset(['test@a.new.domain.com'])
    b = eset(['a.new.domain.com'])
    c = eset(['domain.com'])
    xs = ['test@a.new.domain.com', 'test2@a.new.domain.com', 'test3@another.domain.com', 'test4@domain.us', 'us']
    for s in [a, b, c]:
        print("---> ", s)
        for x in xs:
            print('%s: %s' % (x, x in s))