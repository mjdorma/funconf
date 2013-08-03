funconf - Function Configuration
********************************

funconf simplifies the management of function default keyword values by
seamlessly integrating configuration files into mapping objects which can be
bound to a function that takes variable keyword arguments. 


Project hosting provided by `github.com`_.


Install
=======

Simply run the following::

    > python setup.py install

or `PyPi`_::

    > pip install funconf 


funconf with begins
===================

The motivation for funconf was to build a simple file configuration management
capability that integrates with the command line interface tool `begins`_. 

Taking this example YAML configuration file::

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

And applying it to this simple program::
   
    $ cat demo.py

    import begin
    import funconf 

    config = funconf.Config('my.conf')

    @begin.subcommand
    @config.foo.wraps
    def foo(**k):
        """This is the foo code"""
        print(k)

    @begin.subcommand
    @config.bread.wraps
    def bread(**k):
        """This is the bread code"""
        print(k)

    @begin.start
    @config.wraps
    def main(**k):
        """The program"""
        print(k)


You will end up with the following help from the main::

    $ python demo.py -h
    usage: demo.py [-h] [--foo_bar FOO_BAR] [--bread_butter BREAD_BUTTER]
                   [--foo_moo FOO_MOO] [--bread_milk BREAD_MILK]
                   {bread,foo} ...

    The program 

    optional arguments:
      -h, --help            show this help message and exit
      --foo_bar FOO_BAR     (default: 4)
      --bread_butter BREAD_BUTTER
                            (default: win)
      --foo_moo FOO_MOO, -f FOO_MOO
                            (default: ['how', 'are', 'you'])
      --bread_milk BREAD_MILK, -b BREAD_MILK
                            (default: fail)

    Available subcommands:
      {bread,foo}
        bread               This is the bread code
        foo                 This is the foo code
        

If you check help for foo you get the following::

    $ python demo.py foo --help
    usage: demo.py foo [-h] [--moo MOO] [--bar BAR]

    This is the foo code

    optional arguments:
      -h, --help         show this help message and exit
      --moo MOO, -m MOO  (default: ['how', 'are', 'you'])
      --bar BAR, -b BAR  (default: 4)


Concluding summary:  The default values read into the config object from
my.conf will be overridden by begins when it passes in user defined option
values.  This yields a subtle advantage of, as soon as your program entry has
executed, you now have a simple to use global object which represents the
programs configuration state. 

See the documentation prologue of `funconf.py`_ for more details.


Compatibility
=============

TBA


Change log
==========


* not yet released

.. _github.com: https://github.com/mjdorma/funconf
.. _PyPi: http://pypi.python.org/pypi/funconf
.. _begins: https://github.com/aliles/begins
.. _funconf.py: https://github.com/mjdorma/funconf/blob/master/funconf.py

