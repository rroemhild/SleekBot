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

class CommandBot(object):
    """ Base class for bots that accept commands.
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
        self.add_event_handler("message", self.handle_msg_botcmd, threaded=True)

    def register_botcmd(self, where):
        """ Look in all members of where for botcmd decorated function and add them to the command list
        """
        for name, f in inspect.getmembers(where):
            if inspect.ismethod(f) and hasattr(f, '_botcmd'):
                if f._botcmd['IM']:
                    self.im_commands[f._botcmd['name']] = f
                if f._botcmd['MUC']:                    
                    self.muc_commands[f._botcmd['name']] = f

    def reset_botcmd(self):
        """  Reset bot commands to initial state
        """
        self.im_commands = {}
        self.muc_commands = {}
        self.register_botcmd(self)

        self.owners = set(self.get_member_class_jids('owner'))
        self.admins = set(self.get_member_class_jids('admin'))
        self.members = set(self.get_member_class_jids('member'))
        self.banned = set(self.get_member_class_jids('banned'))
        self.require_membership = self.botconfig.find('require-membership')

    def handle_msg_event(self, msg, command_found):
        """ Performs extra actions on the message.
            Overload this to handle messages in a generic way.
        """
        pass

    def handle_msg_botcmd(self, msg):
        if not self.should_answer_msg(msg):
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
                        logging.debug("appending %s to %s list" % (jid.text, userClass))
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

        return self.should_answer_to_jid(self.get_real_jid(msg))

    def should_answer_to_jid(self, jid):
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
