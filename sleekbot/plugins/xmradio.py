"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

import sys
import re
import traceback
import urllib2

from sleekbot.commandbot import botcmd
from sleekbot.plugbot import BotPlugin


class xmradio(BotPlugin):
    """A plugin for seeing what's on XM Radio."""

    @botcmd(name='xm', usage='[channel number]')
    def handle_xm(self, command, args, msg):
        """Tells you what's on XM.
        Example: !xm 47"""
        try:
            xmChan = xmChannel(args)
            return xmChan.show()
        except:
            traceback.print_exc()
            return "Invalid command. Usage: xm [channel number]"


class xmChannel(object):
    def __init__(self, inputstr):
        datapointer = urllib2.urlopen("http://xmradio.com/padData/pad_provider.jsp?channel=" + inputstr)
        self.data = datapointer.read()
        datapointer.close()

    def show(self):

        begindex = self.data.find("<artist>") + 8
        endex = self.data.find("</artist>") + 0
        artist = self.data[begindex:endex]

        begindex = self.data.find("<songtitle>") + 11
        endex = self.data.find("</songtitle>") + 0
        title = self.data[begindex:endex]

        begindex = self.data.find("<channelname>") + 13
        endex = self.data.find("</channelname>") + 0
        channelName = self.data[begindex:endex]

        begindex = self.data.find("<channelnumber>") + 15
        endex = self.data.find("</channelnumber>") + 0
        channelNumber = self.data[begindex:endex]

        output = channelNumber + " - " + channelName + " is playing \"" + title + "\" by " + artist
        if output.find("<paddata>") > 0:
            raise Exception, "No channel info found."
        return output
