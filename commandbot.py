"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

__author__ = 'Hernan E. Grecco <hernan.grecco@gmail.com>'
__license__ = 'MIT License/X11 license'

import logging
import inspect
import threading
import re

def botcmd(name='', usage='', title='', doc='', IM=True, MUC=True, hidden=False ):
    """ Method decorator to declare a bot command
        The method signature has to be (self, cmd, args, msg):
            cmd  -- string with the command
            args -- string with the arguments
            msg  -- dictionary containing message properties (see SleekXMPP)

            returns reply string

        Decorator arguments:
            name   -- name of the command (default method's name)
            usage  -- one line usage instructions (default empty)
            title  -- one line description of the command
                        (default docstring first line)
            doc    -- extensive description of the command.
                        (default docstring without first line)
            IM     -- command will be available in IM (default True)
            MUC    -- command will be available in MUC (default True)
            hidden -- command will not be displayed in the help (default False)
    """
    def _outer(f):
        def _inner(*args, **kwargs):
            return f(*args, **kwargs)

        if not f.__doc__:
            f.__doc__ = ''

        _inner._botcmd = dict()
        _inner._botcmd['hidden'] = hidden
        _inner._botcmd['name'] = name or f.__name__
        _inner._botcmd['title'] = title or f.__doc__.split('\n', 1)[0] or ''
        _inner._botcmd['doc'] = doc or f.__doc__ or 'undocumented'
        _inner._botcmd['usage'] = usage or ''
        _inner._botcmd['IM'] = IM
        _inner._botcmd['MUC'] = MUC
        return _inner
    return _outer

class botfreetxt(object):
    """ Method decorator to declare a bot free text parser
        The method signature has to be (self, text, msg, command_found, freetext_found):
            text           -- body of the message
            msg            -- dictionary containing message properties
            command_found  -- msg matched a previous botcmd
            freetext_found -- msg matched a previous freetxt
            match          -- result of the regular expression match operaton

            returns reply string

        Decorator arguments:
            priority -- number indicating execution order. Lower is first (default 1)
            regex    -- regex string or regex object to be matched (default None)
    """

    def __init__(self, priority = 1, regex = None):
        self.priority = priority
        if isinstance(regex, str):
            try:
                self.regex = re.compile(regex)
            except:
                self.regex = None
        elif not isinstance(regex, re.RegexObject):
            self.regex = None

    def __call__(self, f):
        def _inner(self_inner, text, msg, command_found, freetext_found, match=None):
            if self.regex:
                match = self.regex.search(text)
                if match:
                    return f(self_inner, text, msg, command_found, freetext_found, match)
                else:
                    return None
            else:
                return f(self_inner, text, msg, command_found, freetext_found)

        if not f.__doc__:
            f.__doc__ = ''

        _inner._botfreetxt = dict()
        _inner._botfreetxt['regex'] = self.regex
        _inner._botfreetxt['priority'] = self.priority
        return _inner


class CommandBot(object):
    """ Base class for bots that accept commands.
        Requires to be coinherited with a class that has the following commands
            send_message
            add_event_handler
            del_event_handler
        as defined in SleekXMPP
        and a property named:
            botconfig -- XML ElementTree from the config file. For example:
                <prefix im='/' muc='!' />
                <users>
                    <owner>
                        <jid>owner1@server.com</jid>
                        <jid>owner2@server.com</jid>
                    </owner>
                    <admin>
                        <jid>trusteduser@server.com</jid>
                    </admin>
                    <member>
                        <jid>arbitrarybotuser@server.com</jid>
                    </member>
                    <banned>
                        <jid>banneduser@server.com</jid>
                    </banned>
                </users>
    """

    def __init__(self, im_prefix = '/', muc_prefix = '!' ):
        prefix = self.botconfig.find('prefix')
        if prefix is None:
            self.im_prefix = im_prefix
            self.muc_prefix = muc_prefix
        else:
            self.im_prefix = prefix.attrib.get('im', im_prefix)
            self.muc_prefix = prefix.attrib.get('muc', muc_prefix)

        self.__event = threading.Event()
        CommandBot.start(self)

    def register_commands(self, obj):
        """ Register bot methods from an object
                obj -- object containing bot methods
        """
        for name, f in inspect.getmembers(where):
            if inspect.ismethod(f) and hasattr(f, '_botcmd'):
                if f._botcmd['IM']:
                    self.im_commands[f._botcmd['name']] = f
                if f._botcmd['MUC']:
                    self.muc_commands[f._botcmd['name']] = f
            elif inspect.ismethod(f) and hasattr(f, '_botfreetxt'):
                self.freetext.heappush((f._botfreetxt['priority'], f))

    def unregister_commands(self, where):
        """ Unregister bot methods from an object
                obj -- object containing bot methods
        """
        for name, f in inspect.getmembers(where):
            if inspect.ismethod(f) and hasattr(f, '_botcmd'):
                if f._botcmd['IM']:
                    del self.im_commands[f._botcmd['name']]
                if f._botcmd['MUC']:
                    del self.muc_commands[f._botcmd['name']]
            elif inspect.ismethod(f) and hasattr(f, '_botfreetxt'):
                self.freetext.remove((f._botfreetxt['priority'], f))

    def start(self):
        """ Mesages will be received and processed
        """
        logging.info("Starting CommandBot")
        CommandBot.reset(self)
        self.add_event_handler("message", self.handle_msg_botcmd, threaded=True)
        CommandBot.resume(self)

    def reset(self):
        """ Reset commands and users
        """
        self.im_commands = {}
        self.muc_commands = {}

        self.freetext = []
        self.register_commands(self)

        self.owners = set(self.get_member_class_jids('owner'))
        self.admins = set(self.get_member_class_jids('admin'))
        self.members = set(self.get_member_class_jids('member'))
        self.banned = set(self.get_member_class_jids('banned'))
        self.require_membership = self.botconfig.find('require-membership') or False
        logging.info('%d owners, %d admins, %d members, %d banned. Require-membership %s' % \
                    ( len(self.owners), len(self.admins), len(self.members), len(self.banned), self.require_membership))

    def stop(self):
        """ Messages will not be received
        """
        logging.info("Stopping CommandBot")
        self.del_event_handler("message", self.handle_msg_botcmd)


    def pause(self):
        """ Received messages will be enqueued for processing
        """
        self.__event.clear()

    def resume(self):
        """ Received messages will be processed
        """
        self.__event.set()

    def handle_msg_event(self, msg, command_found = False, freetext_found = False):
        """ Performs extra actions on the message.
            Overload this to handle messages in a generic way.
        """
        pass

    def handle_msg_botcmd(self, msg):
        """ Message handler. Execution order:
                0.- check should_answer_msg
                1.- Execute matching command (if any)
                2.- Forward msg to registered free text parsers
                3.- Forward msg to handle_msg_event

                msg -- dictionary containing message properties (see SleekXMPP)
        """

        self.__event.wait()

        if not self.should_answer_msg(msg):
            return
        command_found = False
        if msg['type'] == 'groupchat':
            prefix = self.muc_prefix
            commands = self.muc_commands
        else:
            prefix = self.im_prefix
            commands = self.im_commands
        command = msg.get('body', '').strip().split(' ', 1)[0]
        if ' ' in msg.get('body', ''):
            args = msg['body'].split(' ', 1)[-1].strip()
        else:
            args = ''
        if command.startswith(prefix):
            if len(prefix):
                command = command.split(prefix, 1)[-1]
            if command in commands:
                command_found = True
                response = commands[command](command, args, msg)
                self.reply(msg, response)

        freetext_found = False
        for (p, f) in self.freetext:
            response = f(msg['body'], msg, command_found, freetext_found)
            if not response is None:
                self.reply(msg, response)
                freetext_found = True

        self.handle_msg_event(msg, command_found, freetext_found)

    def reply(self, msg, response):
        """ Reply to a message. This will not be needed when msg.reply works for all cases in SleekXMPP
        """

        if msg['type'] == 'groupchat':
            self.send_message("%s" % msg.get('mucroom', ''), response, mtype=msg.get('type', 'groupchat'))
        else:
            self.send_message("%s/%s" % (msg.get('from', ''), msg.get('resource', '')), response, mtype=msg.get('type', 'chat'))

    @botcmd(name='help', usage='help [topic]')
    def handle_help(self, command, args, msg):
        """ Help Commmand
        Returns this list of help commands if no topic is specified.  Otherwise returns help on the specific topic.
        """
        if msg['type'] == 'groupchat':
            commands = self.muc_commands
            prefix   = self.muc_prefix
        else:
            commands = self.im_commands
            prefix   = self.im_prefix

        response = ''
        if args:
            args = args.strip()
            if args in commands:
                f  = commands[args]
                response += '%s -- %s\n' % (args,  f._botcmd['title'])
                response += ' %s\n' % f._botcmd['doc']
                response += "Usage: %s%s %s\n" % (prefix, args,  f._botcmd['usage'])
                return response
            else:
                response += '%s is not a valid command' % args

        response += "Commands:\n"
        for command in sorted(commands.keys()):
            f = commands[command]
            if not f._botcmd['hidden']:
                response += "%s -- %s\n" % (command,  f._botcmd['title'])
        response += "---------\n"
        return response

    def msg_from_owner(self, msg):
        """ Was this message sent from a bot owner?
        """
        jid = self.get_real_jid(msg)
        return jid in self.owners

    def msg_from_admin(self, msg):
        """ Was this message sent from a bot admin?
        """
        jid = self.get_real_jid(msg)
        return jid in self.admins

    def msg_from_member(self, msg):
        """ Was this message sent from a bot member?
        """
        jid = self.get_real_jid(msg)
        return jid in self.members

    def get_member_class_jids(self, user_class):
        """ Returns a list of all jids belonging to users of a given class
        """
        jids = []
        users = self.botconfig.findall('users/' + user_class)
        if users:
            for user in users:
                userJids = user.findall('jid')
                if userJids:
                    for jid in userJids:
                        logging.debug("appending %s to %s list" % (jid.text, user_class))
                        jids.append(jid.text)
        return jids

    def mucnick_to_jid(self, mucroom, mucnick):
        """ Returns the jid associated with a mucnick and mucroom
        """
        if mucroom in self.plugin['xep_0045'].getJoinedRooms():
            logging.debug("Checking real jid for %s %s" %(mucroom, mucnick))
            real_jid = self.plugin['xep_0045'].getJidProperty(mucroom, mucnick, 'jid')
            print real_jid
            if real_jid:
                return real_jid
            else:
                return None
        return None

    def get_real_jid(self, msg):
        """ Returns the real jid of a msg
        """
        if msg['type'] == 'groupchat':
            # TODO detect system message
            return self.mucnick_to_jid(msg['mucroom'], msg['mucnick']).bare
        else:
            if msg['jid'] in self['xep_0045'].getJoinedRooms():
                return self.mucnick_to_jid(msg['mucroom'], msg['mucnick']).bare
            else:
                return msg['from'].bare
        return None

    def should_answer_msg(self, msg):
        """ Checks whether the bot is configured to respond to the sender of a message.
            Overload if needed
        """

        return self.should_answer_jid(self.get_real_jid(msg))

    def should_answer_jid(self, jid):
        """ Checks whether the bot is configured to respond to the specified jid.
            Pass in a muc jid if you want, it'll be converted to a real jid if possible
            Accepts 'None' jids (acts as an unknown user).
        """
        if jid in self.banned:
            return False
        if not self.require_membership:
            return True
        if jid in self.members or jid in self.admins or jid in self.owners:
            return True
        return False
