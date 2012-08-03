"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

__author__ = 'Hernan E. Grecco <hernan.grecco@gmail.com>'
__license__ = 'MIT License/X11 license'

from abc import ABCMeta, abstractmethod, abstractproperty
from functools import wraps, update_wrapper

import logging
import inspect
import threading
import re

from heapq import heappush


def get_class(class_string):
    """ Returns class object specified by a string.
        Arguments:
            class_string -- The string representing a class.

        Raises:
            ValueError if module part of the class is not specified.
    """
    module_name, _, class_name = class_string.rpartition('.')
    if module_name == '':
        raise ValueError('Class name must contain module part.')
    return getattr(__import__(module_name, globals(), locals(),
                             [class_name], -1), class_name)


def denymsg(msg):
    """ Method decorator to add a denymsg property to a method."""
    def _outer(wrapped):
        """ wrapped is the function to be decorated."""
        @wraps(wrapped)
        def _inner(*args, **kwargs):
            """ Returned function."""
            return wrapped(*args, **kwargs)
        _inner._denymsg = msg
        return _inner
    return _outer


def botcmd(name='', usage='', title='', doc='', chat=True, muc=True,
           hidden=False, allow=True):
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
            chat   -- command will be available in im (default True)
            muc    -- command will be available in muc (default True)
            hidden -- command will not be displayed in the help (default False)
            allow  -- callable to check if the user has permissions to run
                        (default True)
        """

    def _outer(wrapped):
        """ wrapped is the function to be decorated."""
        def _nocheck(*args, **kwargs):
            """ No security check. Returns the function.
            """
            return wrapped(*args, **kwargs)

        def _check(*args, **kwargs):
            """ Perform security check and return function if successful
            """
            if allow(args[0].bot, args[-1]):
                return wrapped(*args, **kwargs)
            else:
                return getattr(wrapped, '_denymsg', None) or \
                       getattr(allow, 'denymsg',
                       'You are not allowed to execute this command.')

        # Warning this is not the same as if allow:
        _inner = _nocheck if allow is True else _check
        update_wrapper(_inner, wrapped)
        if not wrapped.__doc__:
            wrapped.__doc__ = ''

        _inner.botcmd_info = dict()
        _inner.botcmd_info['hidden'] = hidden
        _inner.botcmd_info['name'] = name or wrapped.__name__.replace('_', '-')
        _inner.botcmd_info['title'] = title or \
                                      wrapped.__doc__.split('\n', 1)[0] or \
                                      ''
        _inner.botcmd_info['doc'] = doc or wrapped.__doc__ or 'undocumented'
        _inner.botcmd_info['usage'] = usage or ''
        _inner.botcmd_info['chat'] = chat
        _inner.botcmd_info['muc'] = muc
        _inner.botcmd_info['allow'] = allow
        return _inner
    return _outer


def botfreetxt(priority=1, regex=None):
    """ Method decorator to declare a bot free text parser
        The method signature has to be (self, text, msg, command_found, freetext_found, match):
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

    def _outer(wrapped):
        """ wrapped is the function to be decorated."""
        if isinstance(regex, str):
            try:
                cregex = re.compile(regex)
            except TypeError:
                cregex = None
        elif inspect.ismethod(getattr(regex, 'search', None)):
            cregex = regex
        else:
            cregex = None

        def _nocheck(obj, text, msg, command_found, freetext_found):
            """ No regex given. Returns the wrapped function.
            """
            return wrapped(obj, text, msg, command_found, freetext_found, '')

        def _check(obj, text, msg, command_found, freetext_found):
            """ Regex given. If text matches, returns the wrapped function.
            """
            match = cregex.search(text)
            if match:
                return wrapped(obj, text, msg, command_found,
                               freetext_found, match)
            else:
                return None

        _inner = _nocheck if cregex is None else _check
        update_wrapper(_inner, wrapped)

        _inner.botfreetxt_info = dict()
        _inner.botfreetxt_info['regex'] = cregex
        _inner.botfreetxt_info['priority'] = priority
        return _inner
    return _outer


class CommandBot(object):
    """ Base class for bots that accept commands.
        Requires to be coinherited with a class that has the following commands
            send_message
            add_event_handler
            del_event_handler
        as defined in SleekXMPP
        and a property named:
            botconfig -- a dictionary with the configuration.
    """

    __metaclass__ = ABCMeta

    def __init__(self):
        """ Initializes the CommandBot by registering commands in self
            and message handler
        """

        self.chat_prefix = '/'
        self.muc_prefix = '!'

        self.chat_commands = {}
        self.muc_commands = {}
        self.freetext = []
        self.acl = None
        self.require_membership = True

        self.__event = threading.Event()
        CommandBot.start(self)

    @abstractmethod
    def send_message(self, *args, **kwargs):
        """ Sends an XMPP message
        """
        pass

    @abstractmethod
    def add_event_handler(self, name, pointer, threaded=False,
                          disposable=False):
        """ Adds a handler for an event
        """
        pass

    @abstractmethod
    def del_event_handler(self, name, pointer):
        """ Removes a handler for an event.
        """
        pass

    @abstractmethod
    def get_real_jid(self, msg):
        """ Returns the real jid of a msg
        """
        pass

    @abstractmethod
    def mucnick_to_jid(self, mucroom, mucnick):
        """ Returns the jid associated with a mucnick and mucroom
        """

    @abstractproperty
    def botconfig(self):
        """ Configuration as a dictionary
        """
        pass

    def register_commands(self, obj):
        """ Register bot methods from an object
                obj -- object containing bot methods
        """
        for name, fun in inspect.getmembers(obj, inspect.ismethod):
            if hasattr(fun, 'botcmd_info'):
                if fun.botcmd_info['chat']:
                    self.chat_commands[fun.botcmd_info['name']] = fun
                if fun.botcmd_info['muc']:
                    self.muc_commands[fun.botcmd_info['name']] = fun
            elif hasattr(fun, 'botfreetxt_info'):
                heappush(self.freetext, (fun.botfreetxt_info['priority'], fun))

    def unregister_commands(self, obj):
        """ Unregister bot methods from an object
                obj -- object containing bot methods
        """
        for name, fun in inspect.getmembers(obj):
            if hasattr(fun, 'botcmd_info'):
                if fun.botcmd_info['chat']:
                    del self.chat_commands[fun.botcmd_info['name']]
                if fun.botcmd_info['muc']:
                    del self.muc_commands[fun.botcmd_info['name']]
            elif hasattr(fun, 'botfreetxt_info'):
                self.freetext.remove((fun.botfreetxt_info['priority'], fun))

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
        self.chat_prefix = self.botconfig.get('prefixes.chat', '/')
        self.muc_prefix = self.botconfig.get('prefixes.muc', '!')

        self.chat_commands = {}
        self.muc_commands = {}

        self.freetext = []
        self.register_commands(self)
        aclnode = self.botconfig.get('acl', dict())
        self.acl = get_class(aclnode.get('classname', 'acl.ACL')) \
                  (self, aclnode.get('config', None))
        self.acl.update_from_dict(aclnode)
        self.require_membership = self.botconfig.get('require_membership', False)
        logging.info(self.acl.summarize() + \
                     'Require membership %s', self.require_membership)

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

    def handle_msg_event(self, msg, command_found=False, freetext_found=False):
        """ Performs extra actions on the message.
            Overload this to handle messages in a generic way.
        """
        pass

    def handle_msg_botcmd(self, msg):
        """ Message handler. Execution order:
                0.- check should_answer_msg
                1.- Execute matching command (if any)
                2.- Forward msg to red free text parsers
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
            prefix = self.chat_prefix
            commands = self.chat_commands
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
        for name, method in self.freetext:
            response = method(msg['body'], msg, command_found, freetext_found)
            if not response is None:
                freetext_found = True
                self.reply(msg, response)

        self.handle_msg_event(msg, command_found, freetext_found)

    def reply(self, msg, response):
        """ Reply to a message.
        This will not be needed when msg.reply works for all cases in SleekXMPP
        """

        if msg['type'] == 'groupchat':
            self.send_message("%s" % msg['mucroom'], response,
                              mtype=msg.get('type', 'groupchat'))
        else:
            self.send_message("%s/%s" % (msg['from'].bare,
                              msg['from'].resource), response,
                              mtype=msg.get('type', 'chat'))

    @botcmd(name='help', usage='help [topic]')
    def handle_help(self, command, args, msg):
        """ Help Commmand
        Returns this list of help commands if no topic is specified.  Otherwise returns help on the specific topic.
        """
        if msg['type'] == 'groupchat':
            commands = self.muc_commands
            prefix = self.muc_prefix
        else:
            commands = self.chat_commands
            prefix = self.chat_prefix

        response = ''
        args = args.strip()
        if args:
            if args in commands and \
               (commands[args].botcmd_info['allow'] is True or \
               commands[args].botcmd_info['allow'](self, msg)):
                fun = commands[args]
                response += '%s -- %s\n' % (args, fun.botcmd_info['title'])
                response += ' %s\n' % fun.botcmd_info['doc']
                response += 'Usage: %s%s %s\n' % \
                            (prefix, args, fun.botcmd_info['usage'])
                return response
            else:
                response += '%s is not a valid command' % args

        response += "Commands:\n"
        for command in sorted(commands.keys()):
            fun = commands[command]
            if not fun.botcmd_info['hidden'] and \
               (fun.botcmd_info['allow'] is True or \
               fun.botcmd_info['allow'](self, msg)):
                response += "%s -- %s\n" % (command, fun.botcmd_info['title'])
        response += "---------\n"
        return response

    @denymsg('You are not my owner')
    def msg_from_owner(self, msg):
        """ Was this message sent from a bot owner?
        """
        jid = self.get_real_jid(msg)
        return jid in self.acl.owners

    @denymsg('You are not my admin')
    def msg_from_admin(self, msg):
        """ Was this message sent from a bot admin?
        """
        jid = self.get_real_jid(msg)
        return jid in self.acl.owners or jid in self.acl.admins

    @denymsg('You are not a member')
    def msg_from_member(self, msg):
        """ Was this message sent from a bot member?
        """
        jid = self.get_real_jid(msg)
        return jid in self.acl.owners or \
               jid in self.acl.admins or \
               jid in self.acl.users

    def should_answer_msg(self, msg):
        """ Checks whether the bot is configured to respond to
            the sender of a message.
            Overload if needed
        """
        jid = self.get_real_jid(msg)
        if jid in self.acl.banned:
            return False
        if not self.require_membership:
            return True
        if self.msg_from_member(msg):
            return True
        return False


class Mstr(str):
    """ A string class to which properties can be added."""

    def __new__(cls, string):
        return super(Mstr, cls).__new__(cls, string)


class ArgError(Exception):
    """Exception raised for error in the botcmd arguments

    Attributes:
        var  -- variable name
        msg  -- explanation of the error
    """

    def __init__(self, var, msg):
        self.var = var
        self.msg = msg

    def __str__(self):
        return self.msg

    def __repr__(self):
        return self.msg


def parse_args(cargs, syntax, separator=None):
    """ Helper function to parse and cast botcmd arguments.
    Returns a string-like object where each argument is added as a property.

    Arguments:
        args       -- a string containing the arguments
        syntax     -- a tuple of tuples detailing the syntax of args
                        Each tuple contains 2 elements: name of the argument and value.
                        If value is an element, it is used as a default value
                        If value is a list/tuple, the first element is used as default value
                            and the content is used to define valid values
                        The argument type is infered from the default value
                        If the default value is a type, then the argument is mandatory
        separator  -- the separator used to split args (default = spaces, taking consecutives spaces as one)

    """

    if getattr(cargs, 'parsed_', False):
        return cargs
    out = Mstr(cargs)
    cargs = map(str.strip, cargs.strip().split(separator, len(syntax)))
    delta = len(syntax) - len(cargs)
    if delta < 0:
        out.tail_ = cargs[-1]
        cargs = cargs[0:-1]
    else:
        out.tail_ = None
        cargs += [None] * delta

    for arg, syn in zip(cargs, syntax):
        (name, valid) = syn
        if isinstance(valid, (list, tuple)):
            val = valid[0]
        else:
            val = valid

        if isinstance(val, type):
            # The argument is mandatory
            typ = val
            val = None
        else:
            typ = type(val)

        if not arg is None:
            if typ is str:
                val = arg
            else:
                try:
                    val = typ(arg)
                except:
                    raise ArgError(name, '%s cannot be converted to %s' %
                                         (arg, typ.__name__))
            if isinstance(valid, (list, tuple)) and not val in valid:
                raise ArgError(name, '%s is not a valid value for %s. '
                                     'Valid: %s' % (val, name, valid))

        if val is None:
            raise ArgError(name, '%s is a mandatory argument' % name)
        setattr(out, name, val)
    out.parsed_ = True
    return out
