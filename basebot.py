import logging
import inspect

def botcmd(hidden = False, name='', title='', doc='', usage='', IM = True, MUC = True):
  def _outer(f):
    def _inner(*args, **kwargs):
	return f(*args, **kwargs)      
        
    _inner._botcmd = dict()
    _inner._botcmd['hidden'] = hidden
    _inner._botcmd['name'] = name or f.__name__
    _inner._botcmd['title'] = title or f.__doc__.split('\n', 1)[0] or ''
    _inner._botcmd['doc'] = doc or f.__doc__ or 'undocumented'
    _inner._botcmd['usage'] = usage or 'undocumented'
    _inner._botcmd['IM'] = IM
    _inner._botcmd['MUC'] = MUC
    return _inner
  return _outer


class basebot(object):
    def __init__(self):
        self.im_commands = {}
        self.im_prefix = '/'
        self.muc_commands = {}
        self.muc_prefix = '!'
        self.callbacks = []
        self.polls = []
        self.help = []
        self.add_event_handler("message", self.handle_message_event, threaded=True)
        self.add_event_handler("groupchat_message", self.handle_message_event, threaded=True)
        for name, f in inspect.getmembers(self):                        
            if inspect.ismethod(f) and hasattr(f, '_botcmd'):
                self.addHelp(f._botcmd['name'], f._botcmd['title'], f._botcmd['doc'], f._botcmd['usage'])
                if f._botcmd['IM']:                    
                    self.addIMCommand(f._botcmd['name'], f)
                if f._botcmd['MUC']:
                    self.addMUCCommand(f._botcmd['name'], f)
        
    def clearCommands(self):
        self.im_commands = {}
        self.muc_commands = {}
        self.polls = []
        self.help = []
        #TODO Change this to use the decorator
        self.addIMCommand('help', self.handle_help)
        self.addMUCCommand('help', self.handle_help)
        self.addHelp('help', 'Help Command', "Returns this list of help commands if no topic is specified.  Otherwise returns help on the specific topic.", 'help [topic]')
    
    def shouldAnswerToMessage(self, msg):
        """ Checks whether the bot is configured to respond to the sender of a message.
            Overload this if you want ACLs of some description.
        """
        return True
    
    def handle_message_event(self, msg):
        print msg.keys()
        if not self.shouldAnswerToMessage(msg):
            return
        if msg['type'] == 'groupchat':
            prefix = self.muc_prefix
        else:
            prefix = self.im_prefix
        command = msg.get('body', '').split(' ', 1)[0]
        if ' ' in msg.get('body', ''):
            args = msg['body'].split(' ', 1)[-1]
        else:
            args = ''
        if command.startswith(prefix):
            if len(prefix):
                command = command.split(prefix, 1)[-1]
            if command in self.im_commands:
                response = self.im_commands[command](command, args, msg)
                if msg['type'] == 'groupchat':
                    self.sendMessage("%s" % msg.get('mucroom', ''), response, mtype=msg.get('type', 'groupchat'))
                else:
                    self.sendMessage("%s/%s" % (msg.get('from', ''), msg.get('resource', '')), response, mtype=msg.get('type', 'chat'))
        self.handle_event(msg)
            
    
    def handle_event(self, event):
        """ Handle an event
        """
        for callback in self.callbacks:
            for response in callback.evaluate(event):
                response.execute()
            
    @botcmd(name='help', usage='help [topic]')
    def handle_help(self, command, args, msg):
        '''Help Commmand
        Returns this list of help commands if no topic is specified.  Otherwise returns help on the specific topic.
        '''
        response = ''
        if not args:
            response += "Commands:\n"
            for topic in self.help:
                response += "%s -- %s\n" % (topic[0], topic[1])
            args = 'help'
            response += "---------\n"
        found = False
        for topic in self.help:
            if topic[0] == args:
                found = True
                break
        if found:
            response += "%s\n" % topic[1]
            if topic[3]:
                response += "Usage: %s%s\n" % (self.im_prefix, topic[3])
            response += topic[2]
        return response
    
    def addHelp(self, command, title, body, usage=''):
        self.help.append((command, title, body, usage))
    
    def addIMCommand(self, command, pointer):
        self.im_commands[command] = pointer
    
    def addMUCCommand(self, command, pointer):
        self.muc_commands[command] = pointer

    def registerCallback(self, callbackObject):
        """ Register a callback object with the bot.
        """
        self.callbacks.append(callbackObject)

    def connected(self):
	return self.state['connected']
