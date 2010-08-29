#!/usr/bin/env python
"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.


SleekBot is a pluggable Jabber/XMPP bot based on SleekXMPP.
"""

__author__ = 'Hernan E. Grecco <hernan.grecco@gmail.com>'
__license__ = 'MIT License/X11 license'

import logging

from optparse import OptionParser
from sleekbot.sleekbot import SleekBot

if __name__ == '__main__':
    optp = OptionParser()
    optp.add_option('-q','--quiet', help='set logging to ERROR', action='store_const', dest='loglevel', const=logging.ERROR, default=logging.INFO)
    optp.add_option('-d','--debug', help='set logging to DEBUG', action='store_const', dest='loglevel', const=logging.DEBUG, default=logging.INFO)
    optp.add_option('-v','--verbose', help='set logging to COMM', action='store_const', dest='loglevel', const=5, default=logging.INFO)
    optp.add_option("-c","--config", dest="config_file", default="config.xml", help="set config file to use")
    opts,args = optp.parse_args()

    logging.basicConfig(level=opts.loglevel, format='%(levelname)-8s %(message)s')

    global shouldRestart
    shouldRestart = True
    while shouldRestart:
        shouldRestart = False
        logging.info("Loading config file: %s" % opts.config_file)

        plugin_config = {}
        plugin_config['xep_0092'] = {'name': 'SleekBot', 'version': '0.1-dev'}

        bot = SleekBot(opts.config_file, plugin_config=plugin_config)
        bot.connect()
        bot.process(threaded=False)
        while not bot.state['disconnecting']:
            time.sleep(1)
        #this does not work properly. Some thread is runnng

    logging.info("SleekBot finished")

