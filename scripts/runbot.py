#!/usr/bin/env python
"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.


SleekBot is a pluggable Jabber/XMPP bot based on SleekXMPP.
"""

__author__ = 'Hernan E. Grecco <hernan.grecco@gmail.com>'
__license__ = 'MIT License/X11 license'

import os
import logging
import shutil
import sys

from optparse import OptionParser

from sleekbot.sleekbot import SleekBot

if __name__ == '__main__':
    optp = OptionParser(usage = "usage: %prog [options] configuration_file")
    optp.add_option('-n','--new', help='Create a new configuration file', action='store_const', dest='new', const=True, default=False)
    optp.add_option('-q','--quiet', help='set logging to ERROR', action='store_const', dest='loglevel', const=logging.ERROR, default=logging.INFO)
    optp.add_option('-d','--debug', help='set logging to DEBUG', action='store_const', dest='loglevel', const=logging.DEBUG, default=logging.INFO)
    optp.add_option('-v','--verbose', help='set logging to COMM', action='store_const', dest='loglevel', const=5, default=logging.INFO)
    opts,args = optp.parse_args()
    if not args:
        optp.print_help()
        exit()
    if opts.new:
        import sleekbot.sleekbot
        shutil.copy(os.path.join(os.path.dirname(globals()['sleekbot'].__file__ ), 'config_template.xml'), args[0])
        print("\n  A configuration file named %s was created. Edit it and then start your bot by running:\n\n\t runbot.py %s\n" % (args[0], args[0]))
        exit()

    logging.basicConfig(level=opts.loglevel, format='%(levelname)-8s %(message)s')

    sys.path.append(os.path.dirname(os.path.abspath(args[0])))

    global shouldRestart
    shouldRestart = True
    while shouldRestart:
        shouldRestart = False
        logging.info("Loading config file: %s" % args[0])

        plugin_config = {}
        plugin_config['xep_0092'] = {'name': 'SleekBot', 'version': '0.1-dev'}

        bot = SleekBot(args[0], plugin_config=plugin_config)
        bot.connect()
        bot.process(threaded=False)
        while not bot.state['disconnecting']:
            time.sleep(1)
        #this does not work properly. Some thread is runnng

    logging.info("SleekBot finished")

