"""Overview.
=============

This module simplifies the management of function default keyword argument 
values.

:py:mod:`funconf` introduces a special decorator function called
:py:func:`wraps_kwargs`.  This decorator makes it possible to dynamically
define a fixed number of kwargs for a function that takes a variable number of
kwargs.

For configuration, :py:mod:`funconf` borrows from concepts discussed in
Python's core library *ConfigParser*.  A configuration consists of sections
made up of *option:value* entries, or two levels of mappings that take on the
form *section:option:value*.

The file format YAML has been chosen to allow for option values to exist as
different types instead of being restricted to string type values.


The configuration file
----------------------

Example of a simple YAML configuration file:: 

    $ cat my.conf
    #
    # Foo
    #
    foo:
      bar: 4
      moo:
      - how
      - are
      - you

    #
    # Bread
    #
    bread:
      butter: win
      milk: fail

This file contains two sections foo and bread.  foo has two options bar and
moo.  bar is an integer value of 4 and moo is a list of strings containing
``['how', 'are', 'you']``.  

The above configuration could be generated through a process of adding each
option: value into a :py:class:`Config` object then casting it to a string. For
example::

    config = funconf.Config()
    config.set('foo', 'bar', 4)
    config.set('foo', 'bar', ['how', 'are', 'you'])
    config.set('bread', 'butter', 'milk')
    config.set('bread', 'milk', 'fail)
    print(config)


A configuration object
----------------------

The :py:class:`Config` class is the root class container for all of the
configuration sections.  It implements the *MutableMapping* type which allows
it to seamlessly integrate into the :py:func:`wraps_kwargs` function. 

As a dictionary ``dict(config)`` the :py:class:`Config` object looks like::

    {'bread_butter': 'win',
     'bread_milk': 'fail',
     'foo_bar': 4,
     'foo_moo': ['how', 'are', 'you']}
    
Notice how the configuration *section:options* have been concatenated. This
facilitates the simple wrapping of an entire configuration file into the kwargs
of a function.  The following example will print out an equivalent dictionary
to the printout in the previous example. ::  

    @config
    def myfunc(**kwargs):
        print(kwargs)


A configuration section
-------------------------

To access sections and option values the following pattern holds true::

    assert config.bread.milk == 'fail'
    assert config.bread['milk'] == 'fail'
    assert config['bread_milk'] == 'fail'

A section is represented by the :py:class:`ConfigSection` object. This object
implements the *MutableMapping* type in the same way the :py:class:`Config`
object is implemented and is compatible with the :py:func:`wraps_kwargs`
function.  The :py:class:`ConfigSection` represented ``str(config.bread)``
looks like::

    bread:
      butter: win
      milk: fail

Just like the :py:class:`Config` class, the :py:class:`ConfigSection` can be
used as a decorator to a function too. Here is an example::

    @config.bread
    def myfunc(**kwargs):
        print(kwargs)

"""
import functools
from funcsigs import Signature
from funcsigs import Parameter
from collections import MutableMapping
import shlex

import yaml


def wraps_kwargs(fixed_kwargs):
    """Decorate a function to expose a fixed set of defined *key:value* pairs. 
        
    The following example will define a and b for the variable length kwargs 
    input to the function myfunc::

        mydict = {a=4, b=2}
        @wraps_kwargs(mydict)
        def myfunc(**k):
            pass

    There is an attempt to implicitly type cast input values if they differ
    from the type of the default value found in *fixed_kwargs* and if the type
    of the input value is an instance of *basestring*.  The following list
    details how each type is handled:

        int, bool, float:
            If the input value string can not be cast into an int, bool, or
            float, the exception generated during the attempted conversion
            will be raised.

        list:
            The input value string will be split into a list shlex.split.  
            
        other:
            An attempt to convert other types will be made.  If this fails, the
            input value will be passed through in its original string form.

    The *fixed_kwargs* object needs to satisfy the *MutableMapping* interface
    definition. When the wrapped function is called the kwargs passed in are
    used to update the *fixed_kwargs* object. The *fixed_kwargs* object is
    then passed into the wrapped function i.e. ``wrapped(**fixed_kwargs)``. 
    
    :param fixed_kwargs: keyword arguments to be fix into the wrapped function.
    :type fixed_kwargs: mutable mapping
    :rtype: decorated function.
    """
    def decorator(func):
        def wrapper(**kwargs):
            for k, v in fixed_kwargs.items():
                vtype = type(v)
                value = kwargs.get(k, v)
                if not isinstance(value, vtype) and \
                            isinstance(value, basestring):
                    if vtype is list:
                        value = shlex.split(value)
                    elif vtype in [int, bool, float]:
                        try:
                            value = vtype(value)
                        except:
                            msg = "Can not convert %s='%s' to %s" % (k, value,
                                    vtype)
                            raise ValueError(msg)
                    else:
                        try:
                            value = vtype(value)
                        except:
                            pass
                fixed_kwargs[k] = value 
            return func(**fixed_kwargs)
        functools.update_wrapper(wrapper, func)
        parameters = []
        for k, v in fixed_kwargs.items():
            param = Parameter(k, Parameter.KEYWORD_ONLY, default=v)
            parameters.append(param)
        sig = Signature(parameters=parameters)
        wrapper.__signature__ = sig
        return wrapper
    return decorator


class ConfigAttributeError(AttributeError): pass


class ConfigSection(MutableMapping):
    """The :py:class:`ConfigSection` class is a mutable mapping object that
    represents the *option:value* items for a configuration section. 
    
    The following lists the main features of this class:

    * exposes a configuration *option:value* through a standard implementation
      of the *MutableMapping* abstract type.
    * when cast to a string it outputs its state in YAML.
    * as a decorator it utilises the :py:func:`wraps_kwargs` to change
      the defaults of a variable keyword argument function.  
    """

    _dirty = None 
    _options = None
    _section = None
    _reserved = None

    def __init__(self, section, options):
        """Construct a new :py:class:`ConfigSection` object.  
        
        This object represents a section which contains the mappings between
        the section's options and their respective values. 
       
        :param section: defines the name for this section.
        :type section: str
        :param options: is the mapping containing an initialised set of
                        *option:values* 
        :type options: mutable mapping
        """
        self._section = section
        self._options = options
        self._dirty = True

    def __str__(self):
        "Return a YAML formated string object that represents this object."
        return yaml.dump({self._section: dict(self)}, default_flow_style=False)

    def __dir__(self):
        "Return a list of option names and the Base class attributes."
        return dir(super(ConfigSection, self)) + self._options.keys()

    def __getattribute__(self, y):
        """Return a option value where y is the *option* name.  Else, return
        the value of a reserved word.
        """
        if y in ConfigSection._reserved:
            return super(ConfigSection, self).__getattribute__(y)
        else:
            if y not in self._options:
                msg = "%s not defined in %s" % (y, self._section)
                raise ConfigAttributeError(msg)
            return self._options[y]

    def __setattr__(self, x, y):
        "Only attributes that are a reserved work can be set in this object."
        if x in ConfigSection._reserved:
            super(ConfigSection, self).__setattr__(x, y)
        else:
            self[x] = y

    def __delitem__(self, y):
        raise NotImplementedError("Configuration can only be updated or added")

    def __iter__(self):
        "Iterate all of the 'option' keys."
        return self._options.__iter__()

    def __len__(self):
        """Return the number of options defined in this
        :py:class:`ConfigSection` object"""
        return len(self._options)

    def __setitem__(self, x, y):
        "Set the option value of y for x where x is *option*."
        self._dirty = True
        self._options[x] = y

    def __getitem__(self, y):
        "Return the option value for y where y is *option*."
        return self._options[y]

    @property
    def dirty(self):
        """The dirty property is a convenience property which is set when a
        change has occurred to one of the options under this *section*.  Once
        this property is read, it is reset to False.  

        This property is particularly useful if you're software system has the
        ability to change the configuration state during runtime.  It means
        that you no longer need to remember the state of the options, you just
        need to know that when the dirty property is set, there has been a
        change in the configuration for this section. 

        :rtype: boolean value of dirty.
        """
        self._dirty, d = False, self._dirty
        return d

    def __call__(self, func):
        """The :py:class:`ConfigSection` object can be used as a function
        decorator.  
        
        By decorating a function with variable keyword arguments you're
        function's signature will be changed to a fixed set keyword argument
        with the default values defined in this :py:class:`ConfigSection`
        object.  When you're function is called, the values passed in will be
        set inside of this :py:class:`ConfigSection` object (which is also
        reflected when accessing options through the :py:class:`Config`), thus
        maintaining a simple to use global configuration state.
        
        For example::
            
            myconfig = Config('my.conf')

            @myconfig.mysection
            def func(**k):
                pass

        :param func: function to be wrapped.
        :type func: variable keyword argument function 
        :rtype: wrapped function with fixed kwargs bound to this 
                :py:class:`ConfigSection` object.
        """
        return wraps_kwargs(self)(func)


ConfigSection._reserved = set(dir(ConfigSection))


class Config(MutableMapping):
    """The Config class is the root container that represents configuration
    state set programmatically or read in from YAML config files. 
    
    The following lists the main features of this class:

    * aggregates :py:class:`ConfigSection` objects that are accessible through
      attributes.
    * exposes a translation of the configuration into section_option:value
      through a standard implementation of the *MutableMapping* abstract type.
    * when cast to a string it outputs its state in YAML.
    * as a decorator it utilises the :py:func:`wraps_kwargs` to change
      the defaults of a variable keyword argument function.  
    """

    _sections = None
    _reserved = None
    _lookup = None

    def __init__(self, filenames=[]):
        """Construct a new Config object.  
        
        This is the root object for a function configuration set.  It is the
        container for the configuration sections.

        :param filenames: YAML configuration files.
        :type filenames: list of filepaths
        """
        self._sections = {}
        self._lookup = {}
        self.read(filenames)

    def read(self, filenames):
        """Read and parse a filename or a list of filenames.

        Files that cannot be opened are silently ignored; this is designed so
        that you can specify a list of potential configuration file locations
        (e.g. current directory, user's home directory, system wide directory),
        and all existing configuration files in the list will be read.  A
        single filename may also be given.

        :param filenames: YAML configuration files.
        :type filenames: list of filepaths
        :rtype: list of successfully read files.
        """
        if isinstance(filenames, basestring):
            filenames = [filenames]
        read_ok = []
        for filename in filenames:
            try:
                with open(filename) as f:
                    self.load(f)
                read_ok.append(filename)
            except IOError:
                pass
        return read_ok

    def load(self, stream):
        """Parse the first YAML document from stream then load the
        *section:option:value* elements into this :py:class:`Config` object.

        :param stream: the configuration to be loaded using ``yaml.load``.
        :type stream: stream object
        """
        for section, options in yaml.load(stream).items():
            for option, value in options.items():
                self.set(section, option, value)

    def set(self, section, option, value):
        """Set an option.
        
        In the event of setting an option name or section name to a reserved
        word a ValueError will be raised. A complete set of reserved words for
        both section and option can be seen by::

            print(dir(funconf.Config))
            print(dir(funconf.ConfigOption))

        :param section: Name of the section to add the option into.
        :type section: str
        :param option:  Name of the option.
        :type option: str
        :param value:   Value assigned to this option.
        """
        if section in Config._reserved:
            raise ValueError("%s is a reserved Config word" % option)
        if option in ConfigSection._reserved:
            raise ValueError("%s is a reserved ConfigSection word" % option)
        key = "%s_%s" % (section, option)
        self._lookup[key] = (section, option)
        self[key] = value

    def __str__(self):
        "Return a YAML formated string object that represents this object."
        conf = []
        for section_name, section in self._sections.items():
            conf.append("\n#\n# %s\n#" % (section_name.capitalize()))
            conf.append(str(section))
        return "\n".join(conf)

    def __dir__(self):
        "Return a list of section names and the Base class attributes."
        return dir(super(Config, self)) + self._sections.keys()

    def __getattribute__(self, y):
        """Return a section where y is the *section* name.  Else, return the
        value of a reserved word."""
        if y in Config._reserved:
            return super(Config, self).__getattribute__(y)
        else:
            if y not in self._sections:
                msg = "Config object has no section '%s'" % (y)
                raise ConfigAttributeError(msg)
            return self._sections[y]

    def __setattr__(self, x, y):
        "Only attributes that are a reserved work can be set in this object."
        if x in Config._reserved:
            super(Config, self).__setattr__(x, y)
        else:
            raise Exception("Can not set new attributes in Config %s" % x)

    def __delitem__(self, y):
        raise NotImplementedError("Configuration can only be updated or added")

    def __iter__(self):
        "Iterate all of the *section_option* keys."
        return self._lookup.__iter__()

    def __len__(self):
        "Return the number of options defined in this :py:class:`Config` object"
        return len(self._lookup)

    def __setitem__(self, x, y):
        "Set the option value of y for x where x is *section_option*."
        if x not in self._lookup:
            raise ValueError("There is no section for '%s'" % x)
        s, option = self._lookup[x]
        if s not in self._sections:
            self._sections[s] = ConfigSection(s, {})
        section = self._sections[s] 
        section[option] = y

    def __getitem__(self, y):
        "Return the option value for y where y is *section_option*."
        if y not in self._lookup:
            raise ValueError("There is no section for '%s'" % y)
        s, option = self._lookup[y]
        section = self._sections[s]
        return section[option]

    def __call__(self, func):
        """The :py:class:`Config` object can be used as a function decorator.  
        
        By decorating a function with variable keyword arguments you're
        function's signature will be changed to a fixed set keyword argument
        with the default values defined in this :py:class:`Config` object.
        When you're function is called, the values passed in will be set inside
        of this :py:class:`Config` object, thus maintaining a simple to use
        global configuration state.
        
        For example::
            
            myconfig = Config('my.conf')

            @myconfig
            def func(**k):
                pass

        :param func: function to be wrapped.
        :type func: variable keyword argument function 
        :rtype: wrapped function with fixed kwargs bound to this
                :py:class:`Config` object.
        """
        return wraps_kwargs(self)(func) 


Config._reserved = set(dir(Config))
     
