"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

import re
import cPickle
import logging
import random
import thread
import time
import copy

from sleekbot.commandbot import botcmd
from sleekbot.plugbot import BotPlugin
import sleekbot.confighandler as confighandler

SEARCH = """(([Tt]he|[mM]y)[\s\w\-0-9]+ (is|are|can|has|got)|I am|i am|I'm|
(?=^|,|\.\s|\?)?[\w'0-9\-]+ (is|are|can|got|has))[\s\w'0-9\-:$@%^&*]+"""

class Remember(BotPlugin):
    """A plugin to rembember events."""

    def __init__(self, idlemin=60, idlemax=600):
        BotPlugin.__init__(self)
        self._idlemin = idlemin
        self._idlemax = idlemax

    def _on_register(self):
        self.know = []
        self.load_default()
        self.bot.add_event_handler("groupchat_message", \
                                   self.handle_message_event, threaded=True)
        self.search = re.compile(SEARCH)
        self.prep = ["Let's see... %s.", '%s.', 'I know that %s.', \
                     'I heard that %s.', 'Rumor has it that %s.', \
                     'Did you hear that %s?', \
                     'A little bird told me that %s.', '%s?!??!']
        self.running = True
        self.lastroom = None
        self.lastmessage = ''
        thread.start_new(self.idle, tuple())

    def idle(self):
        """ Background execution.
        """
        while self.running:
            time.sleep(random.randint(self._idlemin, self._idlemax))
            if self.lastroom:
                msg = self.lastmessage.split(' ')
                msgs = copy.copy(msg)
                for word in msgs:
                    if len(word) < 5:
                        msg.remove(word)
                while len(msg) > 0:
                    searchword = msg[random.randint(0, len(msg) - 1)]
                    reply = self.search_know(searchword)
                    if not reply:
                        reply = msg.remove(searchword)
                    else:
                        self.bot.send_message(self.lastroom, \
                                              reply, mtype='groupchat')
                        self.lastmessage = ''
                        break

    @botcmd('know')
    def handle_know_request(self, command, args, msg):
        """Get a random tidbit the bot has picked up."""
        if args:
            search = args
        else:
            search = None
        return self.knowledge(search)

    def get_random_know(self):
        """ Returns a random knowledge. """
        return self.know[random.randint(0, len(self.know) - 1)]

    def search_know(self, search):
        """ Searchs for a given word in knowledge base. """
        found = []
        for know in self.know:
            if search in know:
                found.append("%s  " % self.wrap_know(know))
        if not found:
            return False
        found = found[random.randint(0, len(found) - 1)]
        return found

    def knowledge(self, search=None):
        """ Gets knowledge. """
        if len(self.know) > 0:
            if search:
                found = self.search_know(search)
                if not found:
                    found = "I don't know anything about %s." % search
            else:
                found = self.wrap_know(self.get_random_know())
            return found
        return "I know nothing."

    def wrap_know(self, know):
        """ Wraps knoledge. """
        ran = random.randint(0, len(self.prep) - 1)
        txt = "%s" % (self.prep[ran]) % (know,)
        txt = r[0].upper() + r[1:]
        return txt

    def handle_message_event(self, msg):
        """ Listen to all messages in a muc and store information. """
        room = msg['mucroom']
        if msg['message'].startswith('!'):
            return
        self.lastmessage = msg['message']
        self.command = re.compile("^%s.*know.*?" % room)
        match = self.command.search(msg['message'])
        if match:
            self.bot.send_message(msg['mucroom'], self.knowledge(), \
                                  mtype='groupchat')
            return
        match = self.search.search(msg['message'])
        if match:
            who = None
            match = match.group()
            match = match.lower()
            if not match.startswith(('what', 'where', 'why', 'how', \
                                    'when', 'who', 'that', 'it', 'they')):
                for person in self.bot.plugin['xep_0045'].rooms[room]:
                    if person.lower() in msg['message'].lower():
                        match = match.replace("your", "%s's" % person)
                        match = match.replace('you are', "%s is" % person)
                        break
                match = match.replace('my', "%s's" % msg['name'], 1)
                match = match.replace('my', "his")
                match = match.replace('i am', '%s is' % msg['name'])
                match = match.replace("i'm", '%s is' % msg['name'])
                match = match.replace(" i ", ' %s ' % msg['name'])
                match = match.replace("i've", "%s has" % msg['name'])
                match = match.strip()
                if match not in self.know:
                    logging.debug("Appending knowledge: %s" % match)
                    self.know.append(match)
        self.lastroom = room

    def load_default(self):
        """ Loads default database. """
        self.load("remember.dat")

    def save_default(self):
        """ Saves default database. """
        self.save("remember.dat")

    def load(self, filename):
        """ Loads data from filename. """
        try:
            with open(filename, 'rb') as file_:
                self.know = cPickle.load(file_)
        except:
            logging.error("Error loading remember-plugin data: %s", filename)

    def save(self, filename):
        """ Saves data to filename. """
        try:
            with open(filename, 'wb') as file_:
                cPickle.dump(self.know, file_)
        except IOError:
            logging.error("Error saving remember-plugin data: %s", filename)

    def shut_down(self):
        """ Saves current data and exits """
        self.save_default()
        self.running = False
