"""
    store.py - Sleekbot's persistant storage module.
    Copyright (C) 2008 Kevin Smith

    SleekBot is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    SleekBot is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this software; if not, write to the Free Software
    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
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


