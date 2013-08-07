:py:mod:`funconf` with `begins`_
=================================

The motivation for :py:mod:`funconf` was to build a simple file configuration
management capability that integrates with the command line interface tool
`begins`_. 


Walk through
++++++++++++

Taking this example YAML configuration file `demo.conf`_:

.. literalinclude:: examples/demo.conf 

Applying it to this simple program `demo.py`_:

.. literalinclude:: examples/demo.py 


You will end up with the following help from the main::

    $ python demo.py -h
    usage: demo.py [-h] {bread,foo,run} ...

    This is a super dooper program...

    optional arguments:
      -h, --help       show this help message and exit

    Available subcommands:
      {bread,foo,run}
        bread          This is the bread code
        foo            This is the foo code
        run            This is the run command that controls all


Now you can see how the :py:class:`funconf.Config` object has been bound to the
``run()`` function::

    $ python demo.py run -h
    usage: demo.py run [-h] [--foo_bar FOO_BAR] [--bread_butter BREAD_BUTTER]
                       [--foo_moo FOO_MOO] [--bread_milk BREAD_MILK]

    This is the run command that controls all

    optional arguments:
      -h, --help            show this help message and exit
      --foo_bar FOO_BAR     (default: 4)
      --bread_butter BREAD_BUTTER
                            (default: win)
      --foo_moo FOO_MOO, -f FOO_MOO
                            (default: ['how', 'are', 'you'])
      --bread_milk BREAD_MILK, -b BREAD_MILK
                            (default: fail)

Finally, to see how the :py:class:`funconf.ConfigSection` objects foo and bread
have bound to their respective functions::

    $ python demo.py foo --help
    usage: demo.py foo [-h] [--moo MOO] [--bar BAR]

    This is the foo code

    optional arguments:
      -h, --help         show this help message and exit
      --moo MOO, -m MOO  (default: ['how', 'are', 'you'])
      --bar BAR, -b BAR  (default: 4)


Conclusion
++++++++++

The default values read into the :py:class:`funconf.Config` object from
demo.conf will be overridden by `begins`_ when it passes in user defined option
values from the command line.  As soon as your program entry has executed, you
will now have a simple up to date global object which represents the programs
configuration state. 

Find out more in the :py:mod:`funconf` module documentation. 


.. _demo.py: https://github.com/mjdorma/funconf/blob/master/docs/source/examples/demo.py
.. _demo.conf: https://github.com/mjdorma/funconf/blob/master/docs/source/examples/demo.conf
.. _begins: https://github.com/aliles/begins

