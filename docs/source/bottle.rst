Example webapp 
==============

`bottle`_ makes writing a webapp super simple.  `begins`_ makes writing a CLI
to a program super simple. Through this example you will see how 
:py:mod:`funconf` can make managing configuration files super simple.


Taking this example YAML configuration file `webapp.conf`_:

.. literalinclude:: examples/webapp.conf 

Applying it to this simple program `webapp.py`_:

.. literalinclude:: examples/webapp.py 


The configuration changes the default host address to *0.0.0.0*.  In this
program, configuration is applied and overridden in the following order:

* Decorated function's default keyword value.
* Defined configuration options. 
* Environment variables.
* Input command line interface parameters.

The port option has been included into the config file to ensure that the
:py:class:`funconf.Config` object contains the updated *port* value that may
have been set in an environment variable or set through the CLI. Now we have a
neat way of getting the global configuration state for both *host* and *port*
under the ``config.web`` object.


Here is what the help printout should look like for this application::

    $ python webapp.py --help
    usage: webapp.py [--help] [--debug WEBAPP_DEBUG] [--host WEBAPP_HOST]
                     [--port WEBAPP_PORT]

    optional arguments:
      --help                show this help message and exit
      --debug WEBAPP_DEBUG, -d WEBAPP_DEBUG
                            (default: False)
      --host WEBAPP_HOST, -h WEBAPP_HOST
                            (default: 0.0.0.0)
      --port WEBAPP_PORT, -p WEBAPP_PORT
                            (default: 8080)


The following is the output that you'd expect::

    $ python webapp.py 

    #
    # Web
    #
    web:
      host: 0.0.0.0
      port: 8080

    Bottle v0.11.6 server starting up (using WSGIRefServer())...
    Listening on http://0.0.0.0:8080/
    Hit Ctrl-C to quit.


Notice how the configuration object has been updated when we specify a new
value for the port::

    $ python webapp.py --port 8585 
    #
    # Web
    #
    web:
      host: 0.0.0.0
      port: 8585

    Bottle v0.11.6 server starting up (using WSGIRefServer())...
    Listening on http://0.0.0.0:8585/
    Hit Ctrl-C to quit.

The above example demonstrates how the configuration object has implicitly
casted the input value *8585* CLI string into an integer. 




.. _webapp.py: https://github.com/mjdorma/funconf/blob/master/docs/source/examples/webapp.py
.. _webapp.conf: https://github.com/mjdorma/funconf/blob/master/docs/source/examples/webapp.conf
.. _begins: https://github.com/aliles/begins
.. _bottle: http://bottlepy.org
