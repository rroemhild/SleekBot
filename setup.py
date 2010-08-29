#!/usr/bin/env python

import sys

from distutils.core import setup

setup(
    name = "sleekbot",
    packages = ["sleekbot", "sleekbot/plugins"],
    package_data = {"sleekbot": ['config_template.xml']},
    version = "0.1",
    description = "SleekXMPP based bot frameework",
    author = "Hernan E. Grecco",
    author_email = "hernan.grecco@gmail.com",
    url = "http://github.com/hgrecco/SleekBot",
    download_url = "http://github.com/hgrecco/SleekBot/tarball/master",
    keywords = ["xmpp", "bot", "jabber"],
    classifiers = [
        "Programming Language :: Python",
        "Environment :: Other Environment",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Communications :: Chat"
        ],
    requires     = [ 'sleekxmpp'],
    scripts      = [ 'scripts/runbot.py' ],
    long_description = """\
SleekBot
-------------------------------------

SleekBot is an easily extendable Bot for XMPP (aka Jabber, Google Talk, etc)
written in Python using the SleekXMPP library.

"""
)