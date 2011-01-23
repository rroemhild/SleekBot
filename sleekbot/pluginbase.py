"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

__author__ = 'Hernan E. Grecco <hernan.grecco@gmail.com>'
__license__ = 'MIT License/X11 license'

import logging
import inspect

from collections import defaultdict


def call_on_register(plugin_name):
    """ Decorator to relate a plugin method to the event of another plugin
        being registered
            plugin_name -- a plugin name or an iterable with plugin names
    """
    def __outer(wrapped):
        """ wrapped is the function to be decorated. """
        def __inner(*args, **kwargs):
            """ Returned function """
            return wrapped(*args, **kwargs)
        if isinstance(plugin_name, str):
            plugin_name = (plugin_name, )
        __inner._call_on_register = plugin_name
    return __outer


def call_on_unregister(plugin_name):
    """ Decorator to relate a plugin method to the event of another plugin
         being unregistered
            plugin_name -- a plugin name or an iterable with plugin names
    """
    def __outer(wrapped):
        """ wrapped is the function to be decorated. """
        def __inner(*args, **kwargs):
            """ Returned function """
            return wrapped(*args, **kwargs)
        if isinstance(plugin_name, str):
            plugin_name = (plugin_name, )
        __inner._call_on_unregister = plugin_name
    return __outer


class Plugin(object):
    """ A base class for plugins.
    """

    def __init__(self):
        self.__plugin_dict = None

    def about(self):
        """ About the plugin: returns the docstring."""
        return self.__doc__
    
    def _on_register(self):
        """ Called when the plugin is added to the PluginDict.
        Override in your derived class if necessary.
        """
        pass
    
    def _on_unregister(self):
        """ Called when the plugin is removed from the PluginDict.
        Override in your derived class if necessary.
        """
        pass

    def _register_calls(self):
        """ Register methods from this plugin that should be executed only
        if other plugins are present.
        """
        for name, action in inspect.getmembers(self):
            self._register_calls_one(action, '_call_on_register', True)
            self._register_calls_one(action, '_call_on_unregister', False)


    def _register_calls_one(self, action, prop, execute_now):
        """ Register functions in the containing PluginDict,
        to be called when another plugin is registered/unregistered
        """
        pdict = self.__plugin_dict
        if inspect.ismethod(action) and hasattr(action, prop):
            for related in getattr(action, prop):
                if execute_now and related in pdict:
                    action(related)
                getattr(pdict, prop)[related].add((self, action))

    def _get_dict(self):
        """ Gets the containing PluginDict."""
        return self.__plugin_dict

    def _set_dict(self, value):
        """ Sets in the plugin a reference to the containing PluginDict."""
        self.__plugin_dict = value
        if value is None:
            self._on_unregister()
        else:
            self._on_register()
            self._register_calls()       

    plugin_dict = property(fget=_get_dict, fset=_set_dict)


class PluginDict(dict):
    """ A dictionary class to hold plugins.
    """

    def __init__(self, plugin_base_class=Plugin,
                 default_package='plugins'):
        """ Initialize dictionary
                plugin_base_class -- class from which plugins must derive
                                     (default Plugin)
                default_package   -- string specifying where to look for plugins
                                     (default 'plugins')
        """
        super(PluginDict, self).__init__()
        self._plugin_base_class = plugin_base_class
        self._default_package = default_package
        self.__call_on_register = defaultdict(set)
        self.__call_on_unregister = defaultdict(set)
        __import__(default_package)
        self.__imported = set()
        self.__imported.add(default_package)

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
        for event in self.__call_on_register[key]:
            event[1](value)

        super(PluginDict, self).__setitem__(key, value)
        logging.info("%s registered", key)

    def __delitem__(self, key):
        """ Remove plugin from the dictionary
        """
        if key in self:
            current = super(PluginDict, self).__getitem__(key)
            for event in self.__call_on_unregister[key]:
                event[1](current)
            self._unregister_event(key)
            current.plugin_dict = None
            logging.info("%s unregistered", key)
        else:
            logging.warning("Plugin not in dict %s.", key)

        super(PluginDict, self).__delitem__(key)

    def register(self, plugin, config=None, module=None, package=None):
        """ Loads and register a plugin
                plugin  -- plugin name (name of the class)
                config  -- extra configuration (to be handled to the plugin)
                module  -- module where the plugin is declared
                package -- package where the plugin is declared
        """
        try:
            if plugin in self:
                return
            if isinstance(plugin, self._plugin_base_class):
                self[plugin.__class__.__name__] = plugin
            elif isinstance(plugin, str):
                if package is None:
                    package = self._default_package
                elif not package in self.__imported:
                    __import__(package)
                    self.__imported.add(package)
                    logging.debug('Imported package %s', package)
                if module is None:
                    module = plugin.lower()

                imported = __import__("%s.%s" % (package, module),
                                      fromlist=plugin)
                if config is None:
                    self[plugin] = getattr(imported, plugin)()
                else:
                    self[plugin] = getattr(imported, plugin)(**config)

            return True

        except Exception as ex:
            logging.error('Error while registering plugin %s: %s', plugin, ex)

    def register_many(self, include='__all__', exclude=None, config=None):
        """ Register multiple plugins

                include -- plugins names to register (default __init__.__all__)
                exclude -- plugins names to ignored (default empty set)
                config  -- dict plugin_name:config (default empty dict)
        """

        if config is None:
            config = dict()

        if exclude is None:
            exclude = set()

        if not include:
            include = '__all__'

        for plugin in set(include).difference(set(exclude)):
            self.register(plugin, config.get(plugin, {}))

    def reload(self, name):
        """ Reload a registered plugins.
        """
        config = getattr(self[name], 'config', {})
        module = __import__(self[name].__module__, fromlist=name)
        del self[name]
        reload(module)
        self.register(name, config=config, 
                      module=module.__name__.split('.')[-1])

    def reload_all(self):
        """ Reload all registered plugins.
        """

        for plugin in self.keys():
            self.reload(plugin)

    def _unregister_event(self, plugin):
        """ Unregister events associated with a plugin
        """
        for value in self.__call_on_register.values():
            value = set(filter(lambda x: x[0] != plugin, value))
        for value in self.__call_on_unregister.values():
            value = set(filter(lambda x: x[0] != plugin, value))

    def get_modules(self):
        """ Imports and returns a list of modules
        """
        return [__import__(self[name].__module__, fromlist=name)
                for name in self.keys()]


class NotAPluginError(Exception):
    """Exception raised when the object added to PluginDict is
    not a Plugin

    Attributes:
        classname -- name of the class
    """

    def __init__(self, classname):
        super(NotAPluginError, self).__init__()
        self.classname = classname
