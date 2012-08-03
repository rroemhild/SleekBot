"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

import yaml
import json
import logging
import inspect

def parse_config(value):
    """ Parse a config file file and return a dictionary
            value -- the fullpath of a yaml or json file, or a json string
    """

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
    """ An extended dictionary that supports special get/set and:
            obj.prop to access obj['prop']
    """

    def __init__(self, value):
        dict.__init__(self)
        self._last_value = {}
        self.set(value)

    def __getattr__(self, key):
        return self.__getitem__(key)

    def __getitem__(self, key):
        return self.get(key)

    def get(self, key, default=None):
        """ Return the stored value for a given key or a default if not found
            Supports to point notation to safely access a key in a value
            which is a dict
                e.g. obj.get('a.b') = obj['a']['b']
        """
        try:
            val = self
            for akey in key.split('.'):
                val = dict.__getitem__(val, akey)
            return val
        except KeyError:
            return default

    def set(self, value=None):
        """ Set the configuration dictionary to the content of value.
            If value is none, load the last configuration.
        """
        self.clear()
        self.update(parse_config(value or self._last_value))
        if value:
            self._last_value = value


def dict_to_private(obj, dictionary, exist_warn=False):
    """ Add the dict content as private variables of obj
    """
    for key, value in dictionary:
        if exist_warn and obj.hasattr(key):
            logging.warning('%s property already defined '
                             'for object of type %s with value %r',
                             key, type(obj), obj.getattr('_' + key))
        obj.setattr['_' + key] = value

def get_defaults(fun):
    """ Return a dict with the default values for a function arguments
    """
    args, _, _, defaults = inspect.getargspec(fun)
    return dict(zip(args[-len(defaults):], defaults))

