"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

import datetime
import logging
import codecs

DAYS = ['Monday', 'Tuesay', 'Wednesday', 'Thursday', 
        'Friday', 'Saturday', 'Sunday']
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 
          'August', 'September', 'October', 'November', 'December']

class IrssiLogFile(object):
    """ Handle writing to a single irssi log file.
    """
    def __init__(self, muc, file_name):
        """ Create a logfile handler for a given muc and file.
        """
        self.muc = muc
        self.file_name = file_name
        self.logfile = codecs.open(self.file_name, 'a', 'utf-8')

    def datetime_to_timestamp(self, dt):
        """ Convert a datetime to hh:mm
        """
        return "%02d:%02d" % (dt.hour, dt.minute)

    def log_presence(self, presence):
        """ Log the presence to the file.
            Formats:
            join = '20:06 -!- Nick [userhost] has joined #room'
            quit = '19:07 -!- Nick [userhost] has quit [status]'
        """
        values = {}
        values['nick'] = presence['nick']
        values['reason'] = presence.get('status', "")
        values['userhost'] = presence.get('jid', "%s/%s" % 
                                          (presence['room'], presence['nick']))
        values['time'] = self.datetime_to_timestamp(presence['dateTime'])
        values['room'] = '#%s' % presence['room']
        if presence.get('type', None) == 'unavailable':
            line = '%(time)s -!- %(nick)s [%(userhost)s] has quit [%(reason)s]'
        else:
            line = '%(time)s -!- %(nick)s [%(userhost)s] has joined %(room)s'
        self.append_log_line(line % values)

    def log_message(self, message):
        """ Log the message to the file.
            Formats:
            message = '09:43 <+Nick> messagebody'
            action = '10:45  * Nick actionbodies'
            topic = '18:38 -!- Nick changed the topic of #room to: New Topic'
        """
        values = {}
        values['nick'] = message['name']
        values['userhost'] = message['room']
        values['time'] = self.datetime_to_timestamp(message['dateTime'])
        values['room'] = '#%s' % message['room']
        values['body'] = message['message']
        action = False
        topic = False
        if values['body'][:4] == '/me ':
            action = True
        if action:
            values['body'] = values['body'][4:]
            line = '%(time)s  * %(nick)s %(body)s'
        elif topic:
            line = '%(time)s -!- %(nick)s changed the topic ' \
                   'of %(room)s to: %(body)s'
        else:
            line = '%(time)s <%(nick)s> %(body)s'

        self.append_log_line(line % values)

    def log_date_change(self, new_date):
        """ Log a date change.
            Format:
            --- Day changed Thu Aug 16 2007
        """
        values = {}
        values['dayOfWeek'] = DAYS[new_date.weekday()]
        values['day'] = new_date.day
        values['monthName'] = MONTHS[new_date.month - 1]
        values['year'] = new_date.year
        line = "--- Day changed %(dayOfWeek)s %(monthName)s %(day)s %(year)s"
        self.append_log_line(line % values)

    def append_log_line(self, line):
        """ Append the line to the log
        """
        self.logfile.write("%s\n" % line)
        self.logfile.flush()

class IrssiLogs(object):
    
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.about = "Log muc events."
        self.bot.add_event_handler("groupchat_presence", 
                                   self.handle_groupchat_presence, 
                                   threaded=True)
        self.bot.add_event_handler("groupchat_message", 
                                   self.handle_groupchat_message, 
                                   threaded=True)
        self.room_log_files = {}
        self.room_members = {}
        logs = self.config.findall('log')
        self.lastdate = datetime.datetime.now()
        if logs:
            for log in logs:
                room = log.attrib['room']
                file_name = log.attrib['file']
                self.room_log_files[room] = IrssiLogFile(room, file_name)
                self.room_members[room] = []
                logging.info("irssilogs.py script logging %s to %s.",
                             (room, file_name))

    def check_for_date_change(self, date):
        if (date - self.lastdate).days > 0:
            for log in self.room_log_files.values():
                self.lastdate = date
                log.log_date_change(date)

    def handle_groupchat_presence(self, presence):
        """ Monitor MUC presences.
        """
        presence['dateTime'] = datetime.datetime.now()
        self.check_for_date_change(presence['dateTime'])
        if not presence['room'] in self.room_log_files:
            return
        if presence.get('type', None) == 'unavailable' or \
           presence['nick'] not in self.room_members[presence['room']]:
            self.room_log_files[presence['room']].log_presence(presence)
            if presence.get('type', None) == 'unavailable':
                for i in range(0,len(self.room_members[presence['room']])):
                    if self.room_members[presence['room']][i] == presence['nick']:
                        self.room_members[presence['room']].remove(i)
                        break
            else:
                self.room_members[presence['room']].append(presence['nick'])


    def handle_groupchat_message(self, message):
        """ Monitor MUC messages.
        """
        message['dateTime'] = datetime.datetime.now()
        self.check_for_date_change(message['dateTime'])
        if message['room'] in self.room_log_files.keys():
            self.room_log_files[message['room']].log_message(message)


