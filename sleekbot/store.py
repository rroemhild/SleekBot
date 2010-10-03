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

    def __enter__(self):
        self.__con = self.__connect()
        return self.__con.cursor()

    def __exit__(self, type, value, tb):
        if tb is None:
            self.__con.commit()
            self.__con.close()
            self.__con = None
        else:
            self.__con.rollback()
            self.__con.close()
            self.__con = None


class store(object):
    """ Store persistent data in sqlite3.
    """
    def __init__(self, filename):
        self.filename = filename

    def getDb(self):
        """ Return a new DB connection
        """
        return sqlite3.connect(self.filename)

    def context_cursor(self):
        return CMCursor(self.getDb)
