====================================
SleekBot - a extendable Bot for XMPP
====================================


Description
===========

SleekBot is an easily extendable Bot for XMPP (aka Jabber, Google Talk, etc) written in Python.

Plugins, also written in Python, are used to add new commands and text parsers to your Bot. These new functionalities are declared by decorating python functions. Plugins can be added, removed or reloaded without stopping the Bot thereby providing a useful upgrade path.


Requirements
============
* Python 2.5 or newer
* SleekXMPP
* dnspython


Contribute
==========

If you'd like to hack on SleekBot, you can start by forking my repo on GitHub:

http://github.com/hgrecco/SleekBot

Even easier, you can start working directly in the virtual environment that you was created during the installation. The src subdirectory contains a clone of my repo.

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