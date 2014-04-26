"""Overview.
=============

To simplify the management of function default keyword argument values
:py:mod:`funconf` introduces two new decorators. The first decorator 
:py:func:`wraps_parameters` makes it trivial to dynamically define the
default values of parameters to a function.  The second decorator
:py:func:`lazy_string_cast` automatically casts *basestring* values to the type
of the keyword default values found in the function it is wrapping and the type
of the values found in the *key:value* object passed into its constructor. 

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
it to seamlessly integrate into the :py:func:`wraps_parameters` function. 

As a dictionary ``dict(config)`` the :py:class:`Config` object looks like::

    {'bread_butter': 'win',
     'bread_milk': 'fail',
     'foo_bar': 4,
     'foo_moo': ['how', 'are', 'you']}
    
Notice how the configuration *section:options* have been concatenated. This
facilitates the simple wrapping of an entire configuration file into the kwargs
of a function.  The following example will print an equivalent dictionary to
the printout in the previous example. ::  

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
object is implemented and is compatible with the :py:func:`wraps_parameters`
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
from inspect import isfunction, ismethod 
from collections import MutableMapping
try:
    from collections import OrderedDict 
except ImportError:
    from ordereddict import OrderedDict
import shlex
from distutils.util import strtobool
try:
    from inspect import signature, Signature, Parameter
except ImportError:
    from funcsigs import signature, Signature, Parameter 
try:
    basestring = basestring
except NameError:
    basestring = (str, bytes) 
import yaml


def wraps_parameters(default_kwargs, hide_var_keyword=False,
                                     hide_var_positional=False):
    """Decorate a function to define and extend its positional and keyword
    variables.
        
    The following example will redefine myfunc to have defaults of a=4 and b=3::

        mydict = {a=4, b=3}
        @wraps_parameters(mydict)
        def myfunc(a, b=2):
            pass

    The *default_kwargs* object needs to satisfy the *MutableMapping* interface
    definition. When a wrapped function is called the following transforms
    occur over *kwargs* before it is passed into the wrapped function:

        1. *default_kwargs* is updated with new input parameters.
        2. If the wrapped function has a variable keyword argument defined 
           (i.e ``**k``) then the keywords defined by *default_kwargs* that are
           not defined in *kwargs* will be copied into *kwargs*.
        3. If the wrapped function had no variable keyword argument defined,
           then the keyword input parameters that don't belong to the wrapped
           function's parameters list will be discarded.

    :param default_kwargs: kwargs to be fix into the wrapped function.
    :type default_kwargs: mutable mapping
    :param hide_var_keyword: hide the variable keyword parameter.
    :type hide_var_keyword: Boolean value default True.
    :param hide_var_arguments: hide the variable keyword parameter.
    :type hide_var_arguments: Boolean value default True.
    :rtype: decorated function.
    """
    def decorator(func):
        # Build new signature.
        original_sig = signature(func)
        var_keyword = '' 
        var_positional = '' 
        parameters = OrderedDict()
        original_positional = OrderedDict()
        # Add positional arguments and keywords first.
        for name, param in original_sig.parameters.items():
            if param.kind == param.VAR_KEYWORD:
                var_keyword = name
            elif param.kind == param.VAR_POSITIONAL:
                var_positional = name
            else:
                default = default_kwargs.get(name, param.default)
                param = Parameter(name, param.kind, default=default)
                parameters[name] = param
                original_positional[name] = param
        # Add var positional.
        if var_positional:
            parameters[var_positional] = Parameter(var_positional, 
                                                   Parameter.VAR_POSITIONAL)
        # Add remainder defualt_kwargs as keyword only variables.
        for name, value in default_kwargs.items():
            if name not in parameters:
                param = Parameter(name, Parameter.KEYWORD_ONLY, default=value)
                parameters[name] = param
        # Add var keyword.
        if var_keyword:
            parameters[var_keyword] = Parameter(var_keyword,
                                                Parameter.VAR_KEYWORD)
        # Build our inner wrapper signature.
        wrapper_sig = original_sig.replace(parameters=parameters.values())
        # Remove cloaked var arguments.
        if var_positional and hide_var_positional:
            parameters.pop(var_positional)
        if var_keyword and hide_var_keyword:
            parameters.pop(var_keyword)
        cloak_sig = original_sig.replace(parameters=parameters.values())

        # Wrapper function.
        function_defaults = set(original_sig.parameters)
        override_defaults = set(default_kwargs).intersection(function_defaults)
        def wrapper(*args, **kwargs):
            # Build new kwargs and args.
            arguments = OrderedDict(wrapper_sig.bind(*args, **kwargs).arguments)
            kwargs = {}
            updates = {}
            
            # Build the positional arguments. Override func's default values.
            ordered_args = OrderedDict()
            for name in original_positional:
                if name in arguments:
                    ordered_args[name] = arguments[name]
                    if name in default_kwargs:
                        updates[name] = arguments[name]
                elif name in default_kwargs:
                    ordered_args[name] = default_kwargs[name]
                    updates[name] = default_kwargs[name]
            
            # Now handle the keyword only and var arguments
            args = list(ordered_args.values())
            for name in set(arguments).difference(ordered_args):
                value = arguments[name]
                if name == var_positional:
                    args.extend(value)
                elif name == var_keyword: 
                    for k, v in value.items():
                        kwargs[k] = v
                else:
                    # Update keyword only values
                    if name in default_kwargs:
                        updates[name] = value
                    kwargs[name] = value

            default_kwargs.update(updates)
            if var_keyword:
                # Add default_kwargs keyword values not defined in kwargs.
                for k in set(default_kwargs).difference(kwargs):
                    if k not in original_positional:
                        kwargs[k] = default_kwargs[k]
            else:
                # Remove kwargs that func doesn't have defined.
                for k in set(kwargs).difference(function_defaults):
                    kwargs.pop(k)
            return func(*args, **kwargs)

        # Return wrapped up func with the cloaked signature. 
        functools.update_wrapper(wrapper, func)
        wrapper.__signature__ = cloak_sig
        return wrapper
    return decorator


def lazy_string_cast(model_parameters={}, provide_defaults=True):
    """Type cast string input values if they differ from the type of the
    default value found in *model_parameters*.
    
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
        
        @lazy_string_cast
        def main(a=4, b=[4, 2, 55]):
            pass


    Or using :py:func:`lazy_string_cast` with :py:func:`wraps_parameters` to
    define new keyword defaults::

        config = dict(a=6, b=[4])

        @lazy_string_cast(config)
        @wraps_parameters()
        def main(a=4, b=[4, 2, 55]):
            pass

    :param model_parameters: kwargs to model default type values and keys from.
    :type model_parameters: mutable mapping
    :param provide_defaults: If true, use model_parameters to default arguments
                             which are empty.
    :type provide_defaults: Boolean value default True.
    :rtype: decorated function.
    """
    def cast_type_raise(vtype, key, value):
        try:
            value = vtype(value)
        except:
            msg = "Can not convert %s='%s' to %s" % (key, value,
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
        value = shlex.split(value.replace("\\", "_windowsCompat_"))
        value = [a.replace("_windowsCompat_", "\\") for a in value]
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
            return make_cast_func(cast_type_raise, k, 
                                  lambda x: bool(strtobool(x)))
        elif vtype in [int, float]:
            return make_cast_func(cast_type_raise, k, vtype)
        else:
            return make_cast_func(cast_type, k, vtype)

    class StrCast(dict):
        def __call__(self, name, value):
            if isinstance(value, basestring) and name in self:
                return self[name](value)
            else:
                return value

    def decorator(func):
        sig = signature(func)
        var_keyword, var_positional = '', '' 
        positional = []
        parameters = []
        original_defaults = {}
        # Build the StrCast object
        str_cast = StrCast() 
        for name, param in sig.parameters.items():
            if param.default != param.empty:
                if not isinstance(param.default, basestring):
                    str_cast[name] = cast_factory(name, param.default)
                original_defaults[name] = param.default
                default = param.default
            elif param.default == param.empty and name in model_parameters:
                default = model_parameters[name]
            else: 
                default = param.empty 
            parameters.append(Parameter(name, param.kind, default=default))
            if param.kind == param.VAR_KEYWORD:
                var_keyword = name
            elif param.kind == param.VAR_POSITIONAL:
                var_positional = name
            elif param.kind == param.POSITIONAL_OR_KEYWORD:
                positional.append(name)
        for name, value in model_parameters.items():
            if not isinstance(value, basestring):
                str_cast[name] = cast_factory(name, value)

        if provide_defaults:
            sig = sig.replace(parameters=parameters)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            arguments = OrderedDict(sig.bind(*args, **kwargs).arguments)
            # Cast the function's positional arguments.
            ordered_args = OrderedDict()
            for name in positional:
                if name in arguments:
                    ordered_args[name] = str_cast(name, arguments[name])
                elif provide_defaults and name in model_parameters:
                    ordered_args[name] = model_parameters[name]
                else:
                    ordered_args[name] = original_defaults[name]
            args = list(ordered_args.values())
            # Cast the function's keyword arguments.
            kwargs = {}
            for name in set(arguments).difference(ordered_args):
                value = arguments[name]
                if name == var_positional:
                    args.extend(value)
                elif name == var_keyword: 
                    for k, v in value.items():
                        kwargs[k] = str_cast(k, v)
                else:
                    kwargs[name] = str_cast(name, value)
            return func(*args, **kwargs)
        wrapper.__signature__ = sig
        return wrapper

    if isfunction(model_parameters) or ismethod(model_parameters):
        func, model_parameters= model_parameters, {}
        return decorator(func)
    else:
        return decorator


class ConfigAttributeError(AttributeError): pass


class ConfigSection(MutableMapping):
    """The :py:class:`ConfigSection` class is a mutable mapping object that
    represents the *option:value* items for a configuration section. 
    
    The following lists the main features of this class:

        1. Exposes a configuration *option:value* through a standard
           implementation of the *MutableMapping* abstract type.
        2. When cast to a string it outputs YAML.
        3. As a decorator it utilises the :py:func:`wraps_parameters` to change
           the defaults of a variable kwargs function.  
    """
 
    __slots__ = ('_dirty', '_options', '_section', '_reserved')

    def __init__(self, section, options):
        """Construct a new :py:class:`ConfigSection` object.  
        
        This object represents a section which contains the mappings between
        the section's options and their respective values. 
       
        :param section: defines the name for this section.
        :type section: str
        :param options: kwargs to initialise this :py:class:`ConfigSection`'s
                        *option:value* 
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
        return dir(super(ConfigSection, self)) + list(self._options)

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
        "Only attributes that are a reserved words can be set in this object."
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

    def __call__(self, func=None, lazy=True, hide_var_positional=False,
                                             hide_var_keyword=True):
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

        :param func: Decorator parameter. The function or method to be wrapped.
        :type func: function or method 
        :param lazy: Factory parameter. Turns lazy_string_cast on or off.
        :type lazy: Boolean value default True
        :rtype: As a factory returns decorator function. As a decorator
                function returns a decorated function. 
        """
        if func is None:
            return functools.partial(self, lazy=lazy)
        if lazy:
            inner_lazy = lazy_string_cast(provide_defaults=True)(func)
            wrapped = wraps_parameters(self,
                                 hide_var_positional=hide_var_positional,
                                 hide_var_keyword=hide_var_keyword)(inner_lazy)
            return lazy_string_cast(self, provide_defaults=True)(wrapped) 
        else:
            wrapped = wraps_parameters(self,
                                 hide_var_positional=hide_var_positional,
                                 hide_var_keyword=hide_var_keyword)(func)
            return wrapped


ConfigSection._reserved = set(dir(ConfigSection))


class Config(MutableMapping):
    """The Config class is the root container that represents configuration
    state set programmatically or read in from YAML config files. 
    
    The following lists the main features of this class:

        1. Aggregates :py:class:`ConfigSection` objects that are accessible
           through attributes.
        2. Exposes a translation of the configuration into section_option:value
           through a standard implementation of the *MutableMapping* abstract
           type.
        3. When cast to a string it outputs YAML.
        4. As a decorator it utilises the :py:func:`wraps_parameters` to change
           the defaults of a variable kwargs function.  
    """

    __slots__ = ('_sections', '_reserved', '_lookup', '_strict')

    def __init__(self, filenames=[], strict=False):
        """Construct a new Config object.  
        
        This is the root object for a function configuration set.  It is the
        container for the configuration sections.

        :param filenames: YAML configuration files.
        :type filenames: list of filepaths
        :param strict: If True, raise :py:class:`ConfigAttributeError` if a
                       :py:class:`ConfigSection` doesn't exist.
        :type strict: False 
        """
        self._sections = {}
        self._lookup = {}
        self._strict = strict 
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
        return dir(super(Config, self)) + list(self._sections)

    def __getattribute__(self, y):
        """Return a section where y is the *section* name.  Else, return the
        value of a reserved word."""
        if y in Config._reserved:
            return super(Config, self).__getattribute__(y)
        else:
            if y not in self._sections:
                if not self._strict:
                    self._sections[y] = ConfigSection(y, {})
                else:
                    msg = "Config object has no section '%s'" % (y)
                    raise ConfigAttributeError(msg)
            return self._sections[y]

    def __setattr__(self, x, y):
        "Only attributes that are a reserved words can be set in this object."
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
        """Return the number of options defined in this :py:class:`Config`
        object"""
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
            raise KeyError("There is no section for '%s'" % y)
        s, option = self._lookup[y]
        section = self._sections[s]
        return section[option]

    def __call__(self, func=None, lazy=True, hide_var_positional=False,
                                             hide_var_keyword=True):
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

        :param func: Decorator parameter. The function or method to be wrapped.
        :type func: function or method 
        :param lazy: Factory parameter. Turns lazy_string_cast on or off.
        :type lazy: Boolean value default True
        :rtype: As a factory returns decorator function. As a decorator
                function returns a decorated function. 
        """
        if func is None:
            return functools.partial(self, lazy=lazy)
        if lazy:
            inner_lazy = lazy_string_cast(provide_defaults=True)(func)
            wrapped = wraps_parameters(self,
                                 hide_var_positional=hide_var_positional,
                                 hide_var_keyword=hide_var_keyword)(inner_lazy)
            return lazy_string_cast(self, provide_defaults=True)(wrapped) 
        else:
            wrapped = wraps_parameters(self,
                                 hide_var_positional=hide_var_positional,
                                 hide_var_keyword=hide_var_keyword)(func)
            return wrapped


Config._reserved = set(dir(Config))
     
