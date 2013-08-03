"""Function Configuration.

This module simplifies the management of function default keyword argument 
values.

funconf introduces a special decorator function called 'wraps_kwargs'.  This
decorator makes it possible to dynamically define a fixed number of kwargs for
a function that takes a variable number of kwargs.

For configuration, funconf borrows from concepts discussed in Python's core
library ConfigParser.  A configuration in a setup file that consists of
sections, followed by "option: value" entries maintaining a hierarchy of
section: option: value.

The file format YAML has been chosen to allow for option values to exist as
different types instead of being stuck to string values.

Example of a simple YAML configuration file:: 

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
['how', 'are', 'you'].  

The above configuration could be generated through a process of adding each
option: value into a Config object than casting Config to a string. For
example::

    config = funconf.Config()
    config.set('foo', 'bar', 4)
    config.set('foo', 'bar', ['how', 'are', 'you'])
    config.set('bread', 'butter', 'milk')
    config.set('bread', 'milk', 'fail)
    print(config)

The Config class is the root class container for all of the configuration
sections.  It implements the MutableMapping type which allows it to seamlessly
integrate into the 'wraps_kwargs' function. 

As a dictionary the Config object looks like::

    dict(config)

    {'bread_butter': 'win',
     'bread_milk': 'fail',
     'foo_bar': 4,
     'foo_moo': ['how', 'are', 'you']}
    
Notice how the configuration section: options have been concatenated. This
facilitates the simple wrapping of an entire configuration file into the kwargs
of a function.  The following example will print out an equivalent dictionary
to the printout in the previous example.  

    @config.wraps
    def myfunc(**kwargs):
        print(kwargs)

To access sections and option values the following pattern holds true::

    config.bread.milk == 'fail'
    config.bread['milk'] == 'fail'
    config['bread_milk'] == 'fail'

A section is represented by the ConfigSection object. This object implements
the MutableMapping type in the same way the Config object is implemented and is
compatible with the 'wraps_kwargs' function.  The ConfigSection represented as
a string does the following::

    print(config.bread)
    bread:
      butter: win
      milk: fail

The ConfigSection wraps function can be used in the following way::

    @config.bread.wraps
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
    """Decorate a function to expose a fixed set of defined key:value pairs. 
        
    The following example will define a and b for the variable length kwargs 
    input to the function myfunc::

        mydict = {a=4, b=2}
        @wraps_kwargs(mydict)
        def myfunc(**k):
            pass

    1. There is an attempt to implicitly type cast input values if they differ
    from the type of the default value set in fixed_kwargs and if the type of
    the input value is an instance of basestring.  The following list details
    how each type is handled:

        int, bool, float:
            If the input value string can not be cast into an int, bool, or
            float, the exception generated during the attempted conversion
            will be raised.

        list:
            The input value string will be split into a list shlex.split.  
            
        other:
            An attempt to convert other types will be made.  If this fails, the
            input value will be passed through in its original string form.

    2. The 'fixed_kwargs' object is assumed to be a form of MutableMapping.
    This allows the wrapper to update the key:value pairs inside of the
    'fixed_kwargs' object thus capturing the current input values state.
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
                        value = vtype(value)
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

    _dirty = None 
    _options = None
    _section = None
    _reserved = None

    def __init__(self, section, options):
        self._section = section
        self._options = options
        self._dirty = True

    def __str__(self):
        return yaml.dump({self._section: dict(self)}, default_flow_style=False)

    def __dir__(self):
        return dir(super(ConfigSection, self)) + self._options.keys()

    def __getattribute__(self, y):
        if y in ConfigSection._reserved:
            return super(ConfigSection, self).__getattribute__(y)
        else:
            if y not in self._options:
                msg = "%s not defined in %s" % (y, self._section)
                raise ConfigAttributeError(msg)
            return self._options[y]

    def __setattr__(self, x, y):
        if x in ConfigSection._reserved:
            super(ConfigSection, self).__setattr__(x, y)
        else:
            self[x] = y

    def __delitem__(self, y):
        self._dirty = True
        self._options.__delitem__(y)

    def __iter__(self):
        return self._options.__iter__()

    def __len__(self):
        return len(self._options)

    def __setitem__(self, x, y):
        self._dirty = True
        self._options[x] = y

    def __getitem__(self, y):
        return self._options[y]

    @property
    def dirty(self):
        self._dirty, d = False, self._dirty
        return d

    @property
    def wraps(self):
        return wraps_kwargs(self)


ConfigSection._reserved = set(dir(ConfigSection))


class Config(MutableMapping):

    _sections = None
    _reserved = None
    _lookup = None

    def __init__(self, filenames=[]):
        """Construct a new Config object.  See Config.read to see how
        filenames are loaded and handled. 
        """
        self._sections = {}
        self._lookup = {}
        if filenames:
            self.read(filenames)

    def read(self, filenames):
        """Read and parse a filename or a list of filenames.

        Files that cannot be opened are silently ignored; this is
        designed so that you can specify a list of potential
        configuration file locations (e.g. current directory, user's
        home directory, systemwide directory), and all existing
        configuration files in the list will be read.  A single
        filename may also be given.

        Return list of successfully read files.
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
        """Parse the first YAML document from stream and load the relative
        {section:{option:value}} into this Config object.
        """
        for section, options in yaml.load(stream).items():
            for option, value in options.items():
                self.set(section, option, value)

    def set(self, section, option, value):
        "Set an option."
        if section in Config._reserved:
            raise ValueError("%s is a reserved Config word" % option)
        if option in ConfigSection._reserved:
            raise ValueError("%s is a reserved ConfigSection word" % option)
        key = "%s_%s" % (section, option)
        self._lookup[key] = (section, option)
        self[key] = value

    def __str__(self):
        conf = []
        for section_name, section in self._sections.items():
            conf.append("\n#\n# %s\n#" % (section_name.capitalize()))
            conf.append(str(section))
        return "\n".join(conf)

    def __dir__(self):
        return dir(super(Config, self)) + self._sections.keys()

    def __getattribute__(self, y):
        if y in Config._reserved:
            return super(Config, self).__getattribute__(y)
        else:
            if y not in self._sections:
                msg = "%s not defined in %s" % (y, self._section)
                raise ConfigAttributeError(msg)
            return self._sections[y]

    def __setattr__(self, x, y):
        if x in Config._reserved:
            super(Config, self).__setattr__(x, y)
        else:
            raise Exception("Can not set new attributes in Config %s" % x)

    def __delitem__(self, y):
        raise NotImplementedError()

    def __iter__(self):
        return self._lookup.__iter__()

    def __len__(self):
        return len(self._lookup)

    def __setitem__(self, x, y):
        if x not in self._lookup:
            raise ValueError("There is no section for '%s'" % x)
        s, option = self._lookup[x]
        if s not in self._sections:
            self._sections[s] = ConfigSection(s, {})
        section = self._sections[s] 
        section[option] = y

    def __getitem__(self, y):
        if y not in self._lookup:
            raise ValueError("There is no section for '%s'" % y)
        s, option = self._lookup[y]
        section = self._sections[s]
        return section[option]

    @property
    def wraps(self):
        return wraps_kwargs(self) 


Config._reserved = set(dir(Config))
     
