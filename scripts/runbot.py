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
import time

from optparse import OptionParser

from sleekbot.sleekbot import SleekBot, END_STATUS

if __name__ == '__main__':
    OPTP = OptionParser(usage="usage: %prog [options] configuration_file")
    OPTP.add_option('-n', '--new', help='Create a new configuration file',
                    action='store_const', dest='new',
                    const=True, default=False)
    OPTP.add_option('-q', '--quiet', help='set logging to ERROR',
                    action='store_const', dest='loglevel',
                    const=logging.ERROR, default=logging.INFO)
    OPTP.add_option('-d', '--debug', help='set logging to DEBUG',
                    action='store_const', dest='loglevel',
                    const=logging.DEBUG, default=logging.INFO)
    OPTP.add_option('-v', '--verbose', help='set logging to COMM',
                    action='store_const', dest='loglevel', const=5,
                    default=logging.INFO)
    OPTS, ARGS = OPTP.parse_args()
    if not ARGS:
        OPTP.print_help()
        exit()
    if OPTS.new:
        import sleekbot.sleekbot
        shutil.copy(
            os.path.join(os.path.dirname(globals()['sleekbot'].__file__),
            'config_template.yaml'), ARGS[0])
        print("\n  A configuration file named %s was created. Edit it and "
              "then start your bot by running:\n\n\t runbot.py %s\n"
              % (ARGS[0], ARGS[0]))
        exit()

    if OPTS.loglevel == logging.DEBUG:
        fmt = '%(levelname)-8s %(filename)s:%(lineno)-4d: %(message)s'
    else:
        fmt = '%(levelname)-8s %(message)s'

    logging.basicConfig(level=OPTS.loglevel,
                        format=fmt)


    sys.path.append(os.path.dirname(os.path.abspath(ARGS[0])))

    try:
        SHOULD_RESTART = True
        while SHOULD_RESTART:
            SHOULD_RESTART = False
            logging.info('Loading config file: %s', ARGS[0])

            BOT = SleekBot(ARGS[0])
            BOT.start()
            BOT.process(threaded=False)
            while not BOT.state['disconnecting']:
                time.sleep(1)
            #this does not work properly. Some thread is runnng
            SHOULD_RESTART = (BOT.end_status == END_STATUS.restart)
    except KeyboardInterrupt:
        BOT.die()
        logging.info("End requested")

    logging.info("SleekBot finished")
