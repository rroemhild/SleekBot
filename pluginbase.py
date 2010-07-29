import logging
import inspect
from collections import defaultdict

__author__ = 'Hernan E. Grecco <hernan.grecco@gmail.com>'
__license__ = 'MIT License/X11 license'

def call_on_register(plugin_name):
    """ Register this action to be executed when a plugin is added to the dict.
         plugin_name can be an iterable
    """
    def __outer(f):
        def __inner(*args, **kwargs):
            return f(*args, **kwargs)
        if isinstace(plugin_name,  'str'):
            plugin_name = (plugin_name,  )
        __inner._call_on_register = plugin_name
    return __outer

def call_on_unregister(plugin_name):
    """ Register this action to be executed when a plugin is removed from the dict.
         plugin_name can be an iterable
    """
    def __outer(f):
        def __inner(*args, **kwargs):
            return f(*args, **kwargs)
        if isinstace(plugin_name,  'str'):
            plugin_name = (plugin_name,  )
        __inner._call_on_unregister = plugin_name
    return __outer

class Plugin(object):
    """ A base class for plugins.
    """

    def __init__(self):
        pass

    def on_register(self):
        pass

    def on_unregister(self):
        pass

    def _register_calls(self):
        for name, action in inspect.getmembers(self):
            if inspect.ismethod(action) and hasattr(action, '_call_on_register'):
                for related in action._call_on_register:
                    if related in self.__plugin_dict:
                        action(related)
                    self.__plugin_dict._call_on_register[related].add((self, action))
            if inspect.ismethod(action) and hasattr(action, '_call_on_unregister'):
                for related in action._call_on_unregister:
                    if related in self.__plugin_dict:
                        action(related)
                    self.__plugin_dict._call_on_unregister[related].add((self, action))

    def _get_dict(self):
        return self.__plugin_dict

    def _set_dict(self, value):
        self.__plugin_dict = value
        self._register_calls()

    plugin_dict = property(fget = _get_dict, fset = _set_dict)

def default_plugin_factory(aclass, config):
    """ The default factory for Plugin.
    """    
    return aclass()


class PluginDict(dict):
    """ A dictionary class to hold plugins.
    """

    def __init__(self, plugin_base_class = Plugin, default_factory = default_plugin_factory, default_package = 'plugins'):
        super(PluginDict, self).__init__()
        self._plugin_base_class = plugin_base_class
        self._default_factory = default_factory
        self._default_package = defailt_package

    def __getitem__(self, key):
        """ Get a Plugin from the dictionary.
        """
        return super(PluginDict, self).__getitem__(key)

    def __setitem__(self, key, value):
        """ Add a Plugin to the dictionary an call initializers.
        """
        if not isinstance(value, self._plugin_base_class):
            raise NotAPluginError(value.__name__)

        value.plugin_dict = self
        value.on_register()
        for event in self._call_on_register[key]:
            event[1](value)

        return super(PluginDict, self).__setitem__(key, value)


    def __delitem__(self, key):
        """ Call plugin.on_unregister and then remove it form the dictionary
        """
        if key in self:
            current = super(PluginDict, self).__getitem__(key)
            current.on_unregister()
            for event in self._call_on_unregister[key]:
                event[1](current)
            self._degister_calls(key)
        else:
            logging.warning("Plugin not in dict %s." % key)

        super(PluginDict, self).__delitem__(key)


    def register_plugin(self, name, config = {}, package = '__default__'):
        """ Register a plugin from the same directory of this file.
        """
        if name in self:
            return
        if package == '__default__':
            package = self._plugin_package

        module = __import__("%s.%s" % (package, name), fromlist = name)
        self[name] = self._plugin_factory(getattr(module, name),  config)
        self[name].__config = config
        logging.debug("Loaded Plugin %s: %s" % (name, self[name].__doc__.split('\n', 1)[0] or ''))


    def register_plugins(self, include = '__all__', exclude = set(), config = dict()):
        """ Register multiple plugins

        include -- set of plugins names to register or
                   if empty uses __init__.__all__
        exclude -- set of plugins names to ignored. (default = empty set)
        config  -- dict plugin_name:config. (default = empty dict)
        """

        if not include:
            include = __all__

        for plugin in set(include).difference(set(exclude)):
            self.register_plugin(plugin, config.get(plugin, {}))

    def reload_plugin(self, name, config = {}):
        """ Reload a registered plugins.
        """
        config = getattr(self[name], '__config',  {})
        package = self[name].__package__
        del self[name]
        self.register_plugin(name, config,  package)

    def reload_plugins(self):
        """ Reload all registered plugins.
        """

        for plugin in self.keys():
            self.reload_plugin(plugin)

    def _degister_event(self, source):
        for v in self._call_on_register.values():
            v = set(filter(_not_source(source), v))
        for v in self._call_on_unregister.values():
            v = set(filter(_not_source(source), v))

    def _not_source(event, source):
        return not event[0] == source

class NotAPluginError(Exception):
    """Exception raised when the object added to PluginDict is
    not a Plugin

    Attributes:
        classname -- name of the class
    """

    def __init__(self, classname):
        self.classname = classname
