Example webapp 
==============

`bottle`_ makes writing a webapp super simple.  `begins`_ makes writing a CLI
to a program super simple. Through this example you will see how 
:py:mod:`funconf` can make managing configuration files super simple.


Taking this example YAML configuration file `webapp.conf`_:

.. literalinclude:: examples/webapp.conf 

:TODO describe nuances in the defines


Applying it to this simple program `webapp.py`_:

.. literalinclude:: examples/webapp.py 


:TODO walk through the example - describe keyword assignment.


:TODO add CLI output as demo...



.. _webapp.py: https://github.com/mjdorma/funconf/blob/master/docs/source/examples/webapp.py
.. _webapp.conf: https://github.com/mjdorma/funconf/blob/master/docs/source/examples/webapp.conf
.. _begins: https://github.com/aliles/begins
.. _bottle: http://bottlepy.org
