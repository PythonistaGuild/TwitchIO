:orphan:

Installing
============
TwitchIO 2 requires Python 3.7+.
You can download the latest version of Python `here <https://www.python.org/downloads/>`_.


**Windows:**

.. code:: sh

    py -3.9 -m pip install -U twitchio

**Linux:**

.. code:: sh

    python3.9 -m pip install -U twitchio


Debugging
----------
Make sure you have the latest version of Python installed, or if you prefer, a Python version of 3.7 or greater.

If you have have any other issues feel free to search for duplicates and then create a new issue on GitHub with as much detail as
possible. Including providing the output of pip, your OS details and Python version.


Extras
-------
Twitchio has some extra downloaders available to modify the library.
Due to some outdated binaries on the pypi package index, when using Python 3.11+, you'll want to make use of our custom pypi
index for these extras. You can access this index by doing the following (replace your-extra with the extra you want to use):

.. code:: sh

    python3 -m pip install -U twitchio[your-extra] --extra-index-url https://pip.twitchio.dev/

Or, on windows:

.. code:: sh

    py -3.11 -m pip install -U twitchio[your-extra] --extra-index-url https://pip.twitchio.dev/


If you do not wish to use our custom index, you can build the wheels yourself by installing cython through pip prior to installing the extra.
Note that you will need C build tools installed to be able to do this.

Extra: speed
++++++++++++++
The speed extra will install dependancies built in C that are considerably faster than their pure-python equivalents.
You can install the speed extra by doing:

.. code:: sh

    python3 -m pip install -U twitchio[speed] --extra-index-url https://pip.twitchio.dev/

Or, on windows:

.. code:: sh

    py -3.11 -m pip install -U twitchio[speed] --extra-index-url https://pip.twitchio.dev/

Extra: sounds
+++++++++++++++
The sounds extra installs extra dependancies for using the sounds ext.
If you wish to use the sounds ext, you will need to install this extra, which you can do by doing the following:


.. code:: sh

    python3 -m pip install -U twitchio[sounds] --extra-index-url https://pip.twitchio.dev/

Or, on windows:

.. code:: sh

    py -3.11 -m pip install -U twitchio[sounds] --extra-index-url https://pip.twitchio.dev/