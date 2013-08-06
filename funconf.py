"""Overview.
=============

This module simplifies the management of function default keyword argument 
values.

:py:mod:`funconf` introduces two decorators. The first function
:py:func:`wraps_var_kwargs` makes it possible to dynamically define the
default kwargs for a function that takes a variable number of kwargs.  The
second function :py:func:`lazy_string_cast` casts input parameters passed in
based on the default values of the kwargs it was constructed with. 

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
    config.set('bread', 'milk', 'fail')
    print(config)


A configuration object
----------------------

The :py:class:`Config` class is the root class container for all of the
configuration sections.  It implements the *MutableMapping* type which allows
it to seamlessly integrate into the :py:func:`wraps_var_kwargs` function. 

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
object is implemented and is compatible with the :py:func:`wraps_var_kwargs`
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
from collections import MutableMapping
import shlex
from distutils.util import strtobool
try:
    from inspect import signature, Signature, Parameter
except ImportError:
    from funcsigs import signature, Signature, Parameter 
import yaml


def wraps_var_kwargs(kwarg_defaults):
    """Decorate a function to define set of *key:value* pairs and hide the
    variable keyword argument parameter. 
        
    The following example will redefine myfunc to have default kwargs of a=4
    and b=2:: 

        mydict = {a=4, b=2}
        @wraps_var_kwargs(mydict)
        def myfunc(**k):
            pass

    The *kwarg_defaults* object needs to satisfy the *MutableMapping* interface
    definition. When the wrapped function is called the kwargs passed in are
    used to update the *kwarg_defaults* object. The *kwarg_defaults* object is
    then passed into the wrapped function i.e. ``wrapped(**kwarg_defaults)``. 
    
    :param kwarg_defaults: kwargs to be fix into the wrapped function.
    :type kwarg_defaults: mutable mapping
    :rtype: decorated function.
    """
    def decorator(func):
        kwarg_defaults_set = set(kwarg_defaults)
        def wrapper(**kwargs):
            diff = set(kwargs) - kwarg_defaults_set 
            if diff:
                msg = "%s() got an unexpected keyword argument '%s'" % \
                        (func.func_name, "', '".join(diff)) 
                raise TypeError(msg)
            kwarg_defaults.update(kwargs)
            return func(**kwarg_defaults)
        funcsig = signature(func)
        for param in funcsig.parameters.values():
            if param.kind != param.VAR_KEYWORD:
                msg = "Can only wrap variable length keyword arguments"
                raise ValueError(msg)
        functools.update_wrapper(wrapper, func)
        parameters = []
        for k, v in kwarg_defaults.items():
            param = Parameter(k, Parameter.KEYWORD_ONLY, default=v)
            parameters.append(param)
        sig = Signature(parameters=parameters)
        wrapper.__signature__ = sig
        return wrapper
    return decorator


def lazy_string_cast(model_kwargs):
    """Type cast string input values if they differ from the type of the
    default value found in *model_kwargs*.
    
    The following list details how each type is handled:

        int, bool, float:
            If the input value string can not be cast into an int, bool, or
            float, the exception generated during the attempted conversion
            will be raised.

        list:
            The input value string will be split into a list shlex.split.  If
            the default list value in model contains items, the first item is
            sampled an attempt to cast the entire list is made for that type.
            
        other:
            An attempt to convert other types will be made.  If this fails, the
            input value will be passed through in its original string form.
    
    This example demonstrates how :py:func:`lazy_string_cast` can be applied::
        
        default = dict(a=4, b=[4, 2, 55])

        @lazy_string_cast(default)
        def main(a=4, b=[4, 2, 55]):
            pass

    Or using :py:func:`lazy_string_cast` with :py:func:`wraps_var_kwargs`::

        default = dict(a=4, b=[4, 2, 55])

        @lazy_string_cast(default)
        @wraps_var_kwargs(default)
        def main(**k):
            pass

    :param model_kwargs: kwargs to model default type values and keys from.
    :type model_kwargs: mutable mapping
    :rtype: decorated function.
    """
    def cast_type_raise(vtype, key, value):
        try:
            value = vtype(value)
        except:
            msg = "Can not convert %s='%s' to %s" % (k, value,
                    vtype)
            raise ValueError(msg)
        return value

    def cast_type(vtype, key, value):
        try:
            value = vtype(value)
        except:
            pass
        return value

    def cast_list(inner_cast_func, key, value):
        value = shlex.split(value)
        if inner_cast_func is not None:
            value = [inner_cast_func(a) for a in value]
        return value

    def cast_factory(k, v):
        def make_cast_func(func, key, cast_type):
            return lambda value: func(cast_type, key, value)
        vtype = type(v)
        if vtype is list:
            inner_cast_func = None if not v else cast_factory(k, v[0])
            return make_cast_func(cast_list, k, inner_cast_func)
        elif vtype is bool:
            return make_cast_func(cast_type_raise, k, strtobool)
        elif vtype in [int, float]:
            return make_cast_func(cast_type_raise, k, vtype)
        else:
            return make_cast_func(cast_type, k, vtype)

    cast_ctrl = {}
    for k, v in model_kwargs.items():
        cast_ctrl[k] = (type(v), cast_factory(k, v))

    def decorator(func):
        @functools.wraps(func)
        def wrapper(**kwargs):
            for k, v in kwargs.items():
                if k in cast_ctrl:
                    vtype, cast_func = cast_ctrl[k]
                    if not isinstance(v, vtype) and isinstance(v, basestring): 
                        kwargs[k] = cast_func(v)
            return func(**kwargs)
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
    * as a decorator it utilises the :py:func:`wraps_var_kwargs` to change
      the defaults of a variable kwargs function.  
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
            if x in self:
                self[x] = y
            else:
                raise Exception("Can not set new attributes in ConfigSection")

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

        Applying this decorator to a function which takes variable kwargs will
        change its signature to a set of kwargs with default values defined
        using the values in this :py:class:`ConfigSection` object. The input
        kwargs go through the :py:func:`lazy_string_cast` function and are
        passed into this objects update routine.  The wrapped function is
        finally called with the updated values of this object. 

        For example::
            
            myconfig = Config('my.conf')

            @myconfig.mysection
            def func(**k):
                pass

        :param func: function to be wrapped.
        :type func: variable kwargs function 
        :rtype: wrapped function with defined kwargs defaults bound to this 
                :py:class:`ConfigSection` object.
        """
        return lazy_string_cast(self)(wraps_var_kwargs(self)(func)) 


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
    * as a decorator it utilises the :py:func:`wraps_var_kwargs` to change
      the defaults of a variable kwargs function.  
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
        config = yaml.load(stream)
        if not isinstance(config, dict):
            return
        for section, options in config.items():
            if not isinstance(options, dict):
                continue
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
            raise Exception("Options can not be set through this interface")

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
        
        Applying this decorator to a function which takes variable kwargs will
        change its signature to a set of kwargs with default values defined
        using the values in this :py:class:`Config` object. The input kwargs
        go through the :py:func:`lazy_string_cast` function and are passed
        into this objects update routine.  The wrapped function is finally
        called with the updated values of this object. 

        For example::
            
            myconfig = Config('my.conf')

            @myconfig
            def func(**k):
                pass

        :param func: function to be wrapped.
        :type func: variable kwargs function 
        :rtype: wrapped function with defined kwargs bound to this
                :py:class:`Config` object.
        """
        return lazy_string_cast(self)(wraps_var_kwargs(self)(func)) 


Config._reserved = set(dir(Config))
     
