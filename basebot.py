import logging
import inspect

def botcmd(name='', usage='', title='', doc='', IM = True, MUC = True, hidden = False ):
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
        _inner._botcmd['usage'] = usage or _inner._botcmd['name']
        _inner._botcmd['IM'] = IM
        _inner._botcmd['MUC'] = MUC
        return _inner
    return _outer

class botplugin(object):
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.bot.register_botcmd(self)

class basebot(object):
    """ Base class for robots that accept commands.
        Requires to be coinherited with a class that has the following commands:
        - send_message
        - add_event_handler
        as defined in SleekXMPP
    """
    
    def __init__(self, im_prefix = '/', muc_prefix = '!' ):
        self.im_prefix = im_prefix
        self.muc_prefix = muc_prefix

        self.reset_bot()
        #self.add_event_handler("groupchat_message", self.handle_message_event, threaded=True)
        self.add_event_handler("message", self.handle_message_botcmd, threaded=True)

    def register_botcmd(self, where):
        """ Look in all members of where for botcmd decorated function and add them to the command list
        """
        for name, f in inspect.getmembers(where):
            if inspect.ismethod(f) and hasattr(f, '_botcmd'):
                if f._botcmd['IM']:
                    self.im_commands[f._botcmd['name']] = f
                if f._botcmd['MUC']:                    
                    self.muc_commands[f._botcmd['name']] = f

    def reset_bot(self):
        """  Reset bot commands to initial state
        """
        self.im_commands = {}
        self.muc_commands = {}
        self.register_botcmd(self)

    def should_answer_message(self, msg):
        """ Checks whether the bot is configured to respond to the sender of a message.
            Overload this if you want ACLs of some description.
        """
        return True

    def handle_message_event(self, msg, command_found):
        """ Performs extra actions on the message.
            Overload this to handle messages in a generic way.
        """
        pass

    def handle_message_botcmd(self, msg):
        if not self.should_answer_message(msg):
            return
        command_found = False
        if msg['type'] == 'groupchat':
            prefix = self.muc_prefix
            commands = self.muc_commands
        else:
            prefix = self.im_prefix
            commands = self.im_commands
        command = msg.get('body', '').split(' ', 1)[0]
        if ' ' in msg.get('body', ''):
            args = msg['body'].split(' ', 1)[-1]
        else:
            args = ''
        if command.startswith(prefix):
            if len(prefix):
                command = command.split(prefix, 1)[-1]
            if command in commands:
                command_found = True
                response = commands[command](command, args, msg)
                if msg['type'] == 'groupchat':
                    self.sendMessage("%s" % msg.get('mucroom', ''), response, mtype=msg.get('type', 'groupchat'))
                else:
                    self.sendMessage("%s/%s" % (msg.get('from', ''), msg.get('resource', '')), response, mtype=msg.get('type', 'chat'))
                    #msg.reply(response)
        self.handle_message_event(msg, command_found)

    @botcmd(name='help', usage='help [topic]')
    def handle_help(self, command, args, msg):
        """ Help Commmand
        Returns this list of help commands if no topic is specified.  Otherwise returns help on the specific topic.
        """
        if msg['type'] == 'groupchat':
            commands = self.muc_commands
        else:
            commands = self.im_commands
   
        response = ''
        if args:
            if args in commands:
                f  = commands[arg]._botcmd['title']
                response += '%s -- %s\n' % (arg,  f._botcmd['title'])
                response += ' %s\n' % f._botcmd['doc']
                response += "Usage: %s%s\n" % (arg,  f._botcmd['usage'])
                return response
            else:
                response += '%s is not a valid command' % arg

        response += "Commands:\n"
        for command,  f in commands.items():
            response += "%s -- %s\n" % (command,  f._botcmd['title'])
        response += "---------\n"
        return response


