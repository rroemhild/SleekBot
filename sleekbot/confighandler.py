"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

import yaml
import json

def parse_config(value):
    
    if isinstance(value, str):
        if value.endswith('.yaml'):
            with open(value) as file_:
                return yaml.load(file_)
        elif value.endswith('.json'):
            with open(value) as file_:
                return json.load(file_)
        else:
            return json.loads(value)
    elif isinstance(value, dict):
        return value


class ConfigDict(dict):

    def __init__(self, value):
        dict.__init__(self)
        self.set(value)
   
    def __getattr__(self, key):
        return self.__getitem__(key)
    
    def __getitem__(self, key):
        return self.get(key)
    
    def get(self, key, default=None):
        try:
            val = self
            for akey in key.split('.'):
                val = dict.__getitem__(val, akey)
            return val
        except KeyError:
            return default 
        return val
    
    def set(self, value=None):
        self._last_value = value
        self.clear()
        self.update(parse_config(value or self._last_value))

