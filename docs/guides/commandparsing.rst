:orphan:

.. _commandparsing-ref:

Command Parsing
===============
TwitchIO 3 implements a robust and powerful commands extension for easily creating
chat commands in your twitch.tv IRC Channels.

The Basics
~~~~~~~~~~
A basic command signature might look something like this:

.. code-block:: python3

    @commands.command()
    async def test(self, ctx: commands.Context, arg: str) -> None:
        ...


In the above your command is named ``test`` and has one required positional argument ``arg``
which is type hinted as ``str``.


If your ``command_prefix`` was ``?`` you might invoke this command like: ``?test hello``
This will result in ``arg`` being equal to ``"hello"``.


.. note::

    If you don't pass a value E.g. ``?test`` you will get a ``MissingArgumentError``


To solve this issue, you can set a default to your argument, E.g:

.. code-block:: python3

    @commands.command()
    async def test(self, ctx: commands.Context, arg: str = 'Hello World!') -> None:
        ...


Now if you fail to pass a value it will default to ``"Hello World!"``.


.. note::

    The first and second arguments must always be ``self`` and ``ctx``. You can name these
    however you like, but since commands can only be created in the ``Bot`` class or a ``Component``,
    the first argument will always be the instance of the class the command was created in, and ctx will always be a
    ``commands.Context`` object.


Multiple Arguments
~~~~~~~~~~~~~~~~~~
Commands, just like normal Python functions, can have multiple arguments.

Example:

.. code-block:: python3

    @commands.command()
    async def test(self, ctx: commands.Context, arg1: str, arg2: str) -> None:
        ...


The above command would be invoked like, ``?test Hello World!`` which would mean ``arg1`` is equal to ``"Hello"``
and ``arg2`` is equal to ``"World!"``.


.. note::

    Just like normal Python functions, non-default arguments (arguments without a default value),
    can not be placed after a default argument.


Consume Rest Behaviour
~~~~~~~~~~~~~~~~~~~~~~
In TwitchIO there is a behaviour we call ``consume rest``. The consume rest behaviour allows us to specify an argument
that will consume everything passed after all other argument parsing has taken place, into one last argument.

Consider the following:

.. code-block:: python3

    @commands.command()
    async def test(self, ctx: commands.Context, arg: str, *, rest: str) -> None:
        ...


If we were to invoke this command like, ``?test hello this is a test``, ``arg`` would equal to ``"hello"`` and
``rest`` would equal ``"this is a test"``. Of course you can omit the first argument and only pass a consume rest argument, like so:

.. code-block:: python3

    @commands.command()
    async def test(self, ctx: commands.Context, *, rest: str) -> None:
        ...


Which would mean that anything passed when you invoke the command will end up in ``rest``.


.. note::

    You can only have one consume rest argument. It is the final argument and will consume everything that hasn't already
    been parsed into other arguments.


Argument Converters
~~~~~~~~~~~~~~~~~~~
TwitchIO 3 does special type annotation conversions to enable auto converting your arguments in the command signature.
The default argument type is a ``str``. If you don't annotate your arguments, they will be converted to a ``str`` by default.

The following built-in converters exist for TwitchIO 3:

- ``str`` (Default)
- ``int``
- ``bool``
- ``PartialChatter``


For example, if you wanted one of your arguments to be converted to an ``int`` without having to manually do a conversion in your command,
your signature might look like this:


.. code-block:: python3

    @commands.command()
    async def test(self, ctx: commands.Context, arg: int) -> None:
        ...


If you invoke your command with ``?test 123``, ``arg`` will be ``123`` not ``"123"``.

If you invoke your command with ``?test hello``, an ``BadArgumentError`` will be raised, and your command will fail to invoke.
This is because ``hello`` can not be converted to an ``int``.


Lets say you wanted to grab a ``PartialChatter`` object from the channel you are in, to see various information about a user.


.. code-block:: python3

    @commands.command()
    async def test(self, ctx: commands.Context, chatter: twitchio.PartialChatter) -> None:
        print(chatter.colour)


You could invoke your command like ``?test chillymosh``, this will give you the user ``chillymosh`` assuming they were watching your stream,
and print their colour.


You can also make your own converters and use them in your signature. A converter must either be a coroutine (``async def``)
or a class with a ``convert`` coroutine.


Both solutions, take two parameters, ``context`` (``commands.Context``) and ``argument`` (The value being converted).
For example lets make a simple converter to convert a hex string to a Python hex object.


.. code-block:: python3

    async def hex_converter(context: commands.Context, argument: str) -> hex:
        argument = argument.removeprefix('#')

        try:
            value = hex(int(argument, 16))
        except ValueError:
            raise commands.BadArgumentError(f'Could not convert "{argument}" to hex.')

        return value


Now we can use this converter in our command signature:


.. code-block:: python3

    @commands.command()
    async def test(self, ctx: commands.Context, arg: hex_converter) -> None:
        ...


We could invoke this command like, ``?test #C0FFEE``, which will return a Python ``hex`` int.


You could also make a class with a convert coroutine, for example, lets say we wanted to convert our argument to a special class named ``Thing``:


.. code-block:: python3

    class Thing:

        def __init__(self, *, stuff: str):
            self.stuff = stuff

        @classmethod
        async def convert(cls, context: commands.Context, argument: str):
            return cls(stuff=argument)


Now we can use this converter in our command signature:


.. code-block:: python3

    @commands.command()
    async def test(self, ctx: commands.Context, arg: Thing) -> None:
        ...


We could invoke our command like, ``?test secret``, and now ``arg`` will be equal to ``Thing`` and we could print ``arg.stuff`` which will output ``"secret"``.


Of course these are but minimal examples showcasing the basics of how converters work.


Special Arguments
~~~~~~~~~~~~~~~~~
TwitchIO introduces a new type of argument parsing. These arguments make use of the ``positional only`` syntax introduced in Python 3.8.
Every command, by default, has a ``positional_delimiter`` equal to `=`.

You can change this by passing the ``positional_delimiter`` argument in the command decorator.


.. code-block:: python3

    @commands.command(positional_delimiter=':')


To start using special arguments, you must first define them with the ``positional only`` syntax.


.. code-block:: python3

    @commands.command()
    async def test(self, ctx: commands.Context, arg: str, /) -> None:
        ...


Every arg you define before the `/` is positional only, and will make use of the new TwitchIO Special Argument parsing.
Lets take a look at a quick example:


.. code-block:: python3

    @commands.command()
    async def test(self, ctx: commands.Context, user: twitchio.PartialChatter, /) -> None:
        print(user.colour)


In the above example we define a special argument ``user`` with the default delimiter `=`.
We would invoke this command like, ``?test user=chillymosh``.


You can have more than one special argument, and the order of special arguments being passed does not matter, for instance:


.. code-block:: python3

    @commands.command(positional_delimiter=':')
    async def test(self, ctx: commands.Context, user: twitchio.PartialChatter, other: str, /) -> None:
        print(user)
        print(reason)


In the above example we could invoke our command like, ``?test user:chillymosh other:hello`` or ``?test other:hello user:chillymosh``.
Each argument will be sorted for you.


You can also still use other argument types after special arguments, for example:

.. code-block:: python3

    @commands.command()
    async def test(self, ctx: commands.Context, user: twitchio.PartialChatter, /, *, rest: str) -> None:
        print(user)
        print(rest)


In the above example everything will be consume by ``rest`` other than the ``user`` arg.
For example you could invoke your command in the following ways:


- ``?test Hello World! user=chillymosh``
- ``?test user=chillymosh Hello World!``
