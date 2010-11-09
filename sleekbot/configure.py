#!/usr/bin/env python
"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.


SleekBot is a pluggable Jabber/XMPP bot based on SleekXMPP.
"""

__author__ = 'Hernan E. Grecco <hernan.grecco@gmail.com>'
__license__ = 'MIT License/X11 license'

import os
import sys
import shutil

import sleekbot

from xml.etree import ElementTree as ET


class Configure():
    """ SleekBot configure class.
    """
    
    def __init__(self, config_file, home_dir, template='config_template.xml'):
        self.config_file = config_file
        self.home_dir = home_dir
        self.config_template = template
        
    def create(self):
        """ Create the bot config file.
        """
        
        print("\n\tYou are about to create a SleekBot configuration file.\n"
            "\tFirst choose the work directory for the config. Press enter for\n"
            "\tthe default directory or enter \".\" for the current directory.\n"
            )
        
        user_input = raw_input('Directory for configfile [%s]: ' % self.home_dir)
        if user_input:
            home_dir = os.path.abspath(user_input)
        else:
            home_dir = self.home_dir
        
        if not os.path.exists(home_dir):
            os.makedirs(home_dir)
            print("Created %s." % home_dir)
        
        self.home_dir = home_dir
        os.chdir(self.home_dir)
        
        if os.path.exists(os.path.join(home_dir, self.config_file)):
            print("Config file exists.\n")
            sys.exit()
        
        shutil.copy(
            os.path.join(os.path.dirname(globals()['sleekbot'].__file__),
            self.config_template ), self.config_file)
        print("A configuration file named %s was created in %s.\n"
            % (self.config_file, self.home_dir))
        
        user_input = raw_input("Do you want to setup some basic " +
            "configuration settings? [Y/n]: ")
        if not user_input.lower() == 'n':
            self.config()
    
    def config(self):
        """ Configure SleekBot:
        """
        
        from getpass import getpass
        
        config_file = os.path.join(self.home_dir, self.config_file)
        botconfig = ET.parse(config_file)
        
        auth = botconfig.find('auth')
        storage = botconfig.find('storage')
        acl = botconfig.find('acl')
        
        print("\n\tConfigure SleekBot:\n")
        
        user_input = ''
        
        # auth.jid
        user_input = raw_input("JabberID [%s]: " % auth.attrib['jid'])
        if user_input:
            auth.attrib['jid'] = user_input
        
        # auth.password
        user_input = getpass("Password: ")
        if user_input:
            auth.attrib['pass'] = user_input
            
        # auth.priority
        user_input = raw_input("Priority [%s]: " % auth.attrib['priority'])
        if user_input:
            auth.attrib['priority'] = user_input
            
        # auth.server
        user_input = raw_input("Server [%s]: " % auth.attrib['server'])
        if user_input:
            auth.attrib['server'] = user_input
        
        # storage.file
        default_storage_file = self.config_file.split('.')[0] + '.sqlite'
        user_input = raw_input("Storage filename [%s]: " % default_storage_file)
        if user_input:
            storage.attrib['file'] = user_input
        else:
            storage.attrib['file'] = default_storage_file
        
        # ACL storage
        acl_storages = ( (1, 'XML Configfile', 'ACL'),
                         (2, 'Database', 'ACLdb'), )
        default_acl_storage = 1
        print("Select an option where you want to store the user acl.\n")
        for storage in acl_storages:
            print("[%s] %s" % (storage[0], storage[1]))
        user_input = raw_input("ACl Storage [%s]: " % default_acl_storage)
        if user_input:
            choise = int(user_input) - 1
            acl.attrib['classname']  = "acl." + acl_storages[choise][2]
        else:
            choise = default_acl_storage - 1
            acl.attrib['classname']  = "acl." + acl_storages[choise][2]
        
        # write back the configfile
        botconfig.write(config_file)
        
        print("\nSleekBot configfile %s modified.\n" % config_file)
        print("You may now edit the configfile with your prefered editor and setup"
                " some plugins.\n\n")

