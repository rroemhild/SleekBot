====================================
SleekBot - a extendable Bot for XMPP
====================================


Description
===========

SleekBot is an easily extendable Bot for XMPP (aka Jabber, Google Talk, etc) written in Python.

Plugins, also written in Python, are used to add new commands and text parsers to your Bot. These new functionalities are declared by decorating python functions. Plugins can be added, removed or reloaded without stopping the Bot thereby providing a useful upgrade path.


Instalation
===========

The best way to install SleekBot is using virtualenv (http://virtualenv.openplans.org/) and pip (http://pip.openplans.org/). If you don't know what this is, read http://www.b-list.org/weblog/2008/dec/15/pip/.

    pip install -E sleekbot -r http://github.com/hgrecco/SleekBot/raw/master/requirements_pip.txt

Which is roughly equivalent to

    virtualenv --no-site-packages sleekbot
    source sleekbot/bin/activate
    pip install dnspython
    pip install -e git://github.com/fritzy/SleekXMPP.git#egg=sleekxmpp
    pip install -e git://github.com/hgrecco/SleekBot.git#egg=sleekbot
    deactivate


Running
=======

First, activate your virtual environment:

    source sleekbot/bin/activate

Bots are configured using a xml file. Create a template configuration file by running:

    runbot.py -n config.xml

Edit config.xml with your favorite editor. The file is fully documented, so it should be easy to understand what is the purpose of each entry. Among other thing, you will
* Configure username and password of your bot so it can log in to a server
* Configure access control lists
* Select which plugins are going to be loaded
* Select which XEPs your bot is going to support

Run your bot:

    runbot.py config.xml

and talk to it using your favorite XMPP client.


Requirements
============
* Python 2.5 or newer
* SleekXMPP
* dnspython


Contribute
==========

If you'd like to hack on SleekBot, you can start by forking my repo on GitHub:

http://github.com/hgrecco/SleekBot

The best way to get your changes merged back into core is as follows (thanks Gollum):
   1. Clone your fork
   2. Create a thoughtfully named topic branch to contain your change
   3. Hack away
   4. Test, test, test
   5. Document your code.
   6. Do not change the version number, I will do that on my end
   7. If necessary, rebase your commits into logical chunks, without errors
   8. Push the branch up to GitHub
   9. Send me a pull request for your branch


Authors
=======

Hernan E. Grecco <hernan.grecco@gmail.com>

Original by Nathan Fritz and Kevin Smith

See HISTORY.txt for more details