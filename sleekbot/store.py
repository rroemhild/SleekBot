#!/usr/bin/env python
"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

import sqlite3


class CMCursor(object):
    """ Context manager for cursor. On exit commits and close the connection."""

    def __init__(self, call_to_connect):
        self.__connect = call_to_connect
        self.__con = None

    def __enter__(self):
        self.__con = self.__connect()
        return self.__con.cursor()

    def __exit__(self, typ, value, table):
        if table is None:
            self.__con.commit()
            self.__con.close()
            self.__con = None
        else:
            self.__con.rollback()
            self.__con.close()
            self.__con = None

              
class Store(object):
    """ Store persistent data in sqlite3.
    """
    def __init__(self, filename):
        self.filename = filename

    def get_db(self):
        """ Return a new DB connection
        """
        return sqlite3.connect(self.filename)

    def context_cursor(self):
        """ Return a DB cursor with context management
        """
        return CMCursor(self.get_db)
        
    @staticmethod
    def has_table(cur, name):
        """ Checks if a table exists
                cur   -- a cursor
                name  -- the name of the table to check
        """
        cnt = cur.execute("SELECT count(*) FROM sqlite_master " 
                          "WHERE type='table' AND name=?", (name, ))
        return cnt.fetchone()[0] > 0
       