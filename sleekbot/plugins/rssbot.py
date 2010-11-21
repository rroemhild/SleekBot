"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

from html2text import html2text
import feedparser
import xml.sax.saxutils

import logging
import thread
import time
import re
import pickle
import logging

from sleekbot.commandbot import botcmd, botfreetxt
from sleekbot.commandbot import parse_args, ArgError
from sleekbot.plugbot import BotPlugin

class RSSBot(BotPlugin):
    """ Periodically sends an rss summary to a MUC
    """
    
    def _on_register(self):
        """ Reads config file and create thread to manage feeds
        """
        self.rss_cache = {}
        feeds = self.config.findall('feed')
        self.threads = {}
        self.shutting_down = False
        if not feeds:
            return
        for feed in feeds:
            url, ref = feed.attrib['url'], feed.attrib['refresh']
            logging.info("rssbot.py script starting with feed %s.", url)
            rooms_xml = feed.findall('muc')
            if not rooms_xml:
                continue
            rooms = []
            for room_xml in rooms_xml:
                rooms.append(room_xml.attrib['room'])
            logging.info("Creating new thread to manage feed.")
            self.threads[url] = thread.start_new(self.loop, 
                                                 (url, ref, rooms))

    def shut_down(self):
        """ Shuts down the RSS plugin
        """
        self.shutting_down = True
        logging.info("Shutting down RSSBot plugin")
        #for feed in self.threads.keys():
        #    logging.info("rssbot.py killing thread for feed %s." % feed)
        #    self.threads[feed].exit()

    def loop(self, feed_url, refresh, rooms):
        """ The main thread loop that polls an rss feed 
            with a specified frequency
        """
        self.load_cache(feed_url)
        while not self.shutting_down:
            if self.bot['xep_0045']:
                logging.debug("Fetching feed url: %s", feed_url)
                feed = feedparser.parse(feed_url)
                for item in feed['entries']:
                    if feed_url not in self.rss_cache.keys():
                        self.rss_cache[feed_url] = []
                    if item['title'] in self.rss_cache[feed_url]:
                        continue
                    #print u"found new item %s" % item['title']
                    for muc in rooms:
                        if muc in self.bot['xep_0045'].getJoinedRooms():
                            #print u"sending to room %s" %muc
                            self.send_item(item, muc, feed['channel']['title'])
                    self.rss_cache[feed_url].append(item['title'])
                    #print u"remembering new item %s" % item['title']
                    logging.debug("Saving updated feed cache for %s" , feed_url)
                    self.save_cache(feed_url)
            time.sleep(float(refresh)*60)

    def send_item(self, item, muc, feed_name):
        """ Sends a summary of an rss item to a specified muc.
        """
        #for contentKey in ['summary','value', '']:
        #    if item.has_key(contentKey):
        #        break
        #if contentKey == '':
        #    print "No content found for item"
        #    return
        #print u"found content in key %s" % contentKey
        if 'content' in item:
            content = xml.sax.saxutils.escape(item['content'][0].value)
            content = item['content'][0].value
        else:
            content = ''
        text = html2text("Update from feed %s\n%s\n%s" % 
                         (feed_name, xml.sax.saxutils.escape(item['title']), content))
        self.bot.send_message(muc, text, mtype='groupchat')

    def cache_filename(self, feed_url):
        """ Returns the filename used to store the cache for a feed_url
        """
        rep = re.compile('\W')
        return "rsscache-%s.dat" % rep.sub('', feed_url)

    def load_cache(self, feed):
        """ Loads the cache of entries
        """
        try:
            with open(self.cache_filename(feed), 'rb') as file_:
                self.rss_cache[feed] = pickle.load(file_)
        except IOError:
            logging.error("Error loading rss data %s", 
                          self.cache_filename(feed))

    def save_cache(self, feed):
        """ Saves the cache of entries
        """
        try:
            with open(self.cache_filename(feed), 'wb') as file_:
                pickle.dump(self.rss_cache[feed], file_)
        except IOError:
            logging.error("Error loading rss data %s", 
                          self.cache_filename(feed))
