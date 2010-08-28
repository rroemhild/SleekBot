"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

import logging
import datetime, time

from commandbot import botcmd
from plugbot import BotPlugin

class uptime(BotPlugin):
    """A plugin to display the uptime of the bot."""

    def on_register(self):
        self.started = datetime.timedelta(seconds = time.time())

    @botcmd('uptime')
    def handle_uptime(self, command, args, msg):
        """See how long the bot has been up."""
        now = datetime.timedelta(seconds = time.time())
        diff = now - self.started
        days = diff.days
        seconds = diff.seconds
        weeks = hours = minutes = 0
        weeks = days / 7
        days -= weeks * 7
        hours = seconds / 3600
        seconds -= hours * 3600
        minutes = seconds / 60
        seconds -= minutes * 60
        return "%s weeks %s days %s hours %s minutes %s seconds" % (weeks, days, hours, minutes, seconds)
