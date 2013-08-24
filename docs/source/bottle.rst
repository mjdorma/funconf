Example webapp 
==============

`bottle`_ makes writing a webapp super simple.  `begins`_ makes writing a CLI
to a program super simple. Through this example you will see how 
:py:mod:`funconf` can make managing configuration files super simple.


Taking this example YAML configuration file `webapp.conf`_:

.. literalinclude:: examples/webapp.conf 

Applying it to this simple program `webapp.py`_:

.. literalinclude:: examples/webapp.py 


Applying the above configuration to this application will override the host
parameter default value found in the function declaration from *127.0.0.1* to
*0.0.0.0* and port value from *8080* to *8585*.  In this program, configuration
is applied and overridden in the following order:

1. Decorated function's default keyword value.
2. Defined configuration options. 
3. Environment variables.
4. Input command line interface parameters.

The port option has been included into the config file to ensure that the
:py:class:`funconf.Config` object contains the *port* value that has been
provided by `begins`_. Now we have a neat way of storing and accessing the
application's global configuration state for both *host* and *port* under the
``config.web`` object.


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
                            (default: 8585)


The following is the output that you'd expect::

    $ python webapp.py 

    #
    # Web
    #
    web:
      host: 0.0.0.0
      port: 8585

    Bottle v0.11.6 server starting up (using WSGIRefServer())...
    Listening on http://0.0.0.0:8585/
    Hit Ctrl-C to quit.


In the example below, notice how the configuration object has been updated when
we specify a new value for the port through the command line interface::

    $ python webapp.py --port 8787 
    #
    # Web
    #
    web:
      host: 0.0.0.0
      port: 8787

    Bottle v0.11.6 server starting up (using WSGIRefServer())...
    Listening on http://0.0.0.0:8787/
    Hit Ctrl-C to quit.

The above example also demonstrates how the configuration object has implicitly
casted the input value *8787* CLI string into an integer. 




.. _webapp.py: https://github.com/mjdorma/funconf/blob/master/docs/source/examples/webapp.py
.. _webapp.conf: https://github.com/mjdorma/funconf/blob/master/docs/source/examples/webapp.conf
.. _begins: https://github.com/aliles/begins
.. _bottle: http://bottlepy.org
