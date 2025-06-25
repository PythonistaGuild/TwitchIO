.. _debugging:

.. currentmodule:: twitchio

Debugging
#########

Most issues can be resolved by checking the :ref:`faqs` or by asking in our `Discord <https://discord.gg/RAKc3HF>`_.

If you believe you have found a bug or issue with the library please make an issue on `GitHub <https://github.com/PythonistaGuild/TwitchIO/issues>`_.


Logging
--------

To make it easier for us to debug your issue, we will often ask for DEBUG level logging. You can easily setup logging with the
:func:`~twitchio.utils.setup_logging` function.

.. code:: python3
    
    import logging
    import twitchio

    handler = logging.FileHandler(filename='twitchio.log', encoding='utf-8', mode='w')
    twitchio.utils.setup_logging(level=logging.DEBUG, handler=handler)


You should only need to call this function once, before the bot is started.

Capture and include logs leading upto and shortly after the issue. Please note this file can get very large very quickly and you
may need to setup a rotating logger or monitor its size.


Version/System Information
--------------------------

We will also often ask for your system information and versions of various dependencies. To make this easier you can run the following
command in the environment TwitchIO is currently installed.

**Windows:**

``py -m twitchio --version``


**Linux:**

``python -m twitchio --version``

Please make sure to copy the whole output of this command as it is all useful.


Minimum Reproducible Example
----------------------------

Please have ready and include a minimal example of how to reproduce your issue, including any required steps needed when asking for help.
This allows us to help more effeciently.
