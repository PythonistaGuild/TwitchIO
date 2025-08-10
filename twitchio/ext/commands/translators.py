"""
MIT License

Copyright (c) 2017 - Present PythonistaGuild

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any, Generic, TypeVar


if TYPE_CHECKING:
    from .context import Context


T = TypeVar("T")


__all__ = ("Translator",)


class Translator(Generic[T], abc.ABC):
    """Abstract Base Class for command translators.

    This class allows you to implement logic to translate messages sent via the :meth:`.commands.Context.send_translated`
    method in commands or anywhere :class:`.commands.Context` is available.

    You should pass your implemented class to the :func:`.commands.translator` decorator on top of a :class:`~.commands.Command`.

    .. important::

        You must implement every method of this ABC.
    """

    @abc.abstractmethod
    def get_langcode(self, ctx: Context[Any], name: str) -> T | None:
        """Method which is called when :meth:`.commands.Context.send_translated` is used on a :class:`.commands.Command`
        which has an associated Translator, to determine the ``langcode`` which should be passed to :meth:`.translate` or ``None``
        if the content should not be translated.

        By default the lowercase ``name`` or ``alias`` used to invoke the command is passed alongside :class:`.commands.Context`
        to aid in determining the ``langcode`` you should use.

        You can use any format or type for the language codes. We recommend using a recognized system such as the ``ISO 639``
        language code format as a :class:`str`.

        Parameters
        ----------
        ctx: commands.Context
            The context surrounding the command invocation.
        name: str
            The ``name`` or ``alias`` used to invoke the command. This does not include the prefix, however if you need to
            retrieve the prefix see: :attr:`.commands.Context.prefix`.

        Returns
        -------
        Any
            The language code to pass to :meth:`.translate`.
        None
            No translation attempt should be made with :meth:`.translate`.

        Example
        -------

        .. code:: python3

            # For example purposes only the "get_langcode" method is shown in this example...
            # The "translate" method must also be implemented...

            class HelloTranslator(commands.Translator[str]):
                def __init__(self) -> None:
                    self.code_mapping = {"hello": "en", "bonjour": "fr"}

               def get_langcode(self, ctx: commands.Context, name: str) -> str | None:
                   # Return a default of "en". Could also be ``None`` to prevent `translate` being called and to
                   # send the default message...
                   return self.code_mapping.get(name, "en")


            @commands.command(name="hello", aliases=["bonjour"])
            @commands.translator(HelloTranslator)
            async def hello_command(ctx: commands.Context) -> None:
                await ctx.send_translated("Hello!")
        """

    @abc.abstractmethod
    async def translate(self, ctx: Context[Any], text: str, langcode: T) -> str:
        """|coro|

        Method used to translate the content passed to :meth:`.commands.Context.send_translated` with the language code returned from
        :meth:`.get_langcode`. If ``None`` is returned from :meth:`.get_langcode`, this method will not be called and the
        default content provided to :meth:`~.commands.Context.send_translated` will be sent instead.

        You could use this method to call a local or external translation API, retrieve translations from a database or local
        mapping etc.

        This method must return a :class:`str`.

        Parameters
        ----------
        ctx: commands.Context
            The context surrounding the command invocation.
        text: str
            The content passed to :meth:`~.commands.Context.send_translated` which should be translated.
        langcode: Any
            The language code returned via :meth:`.get_langcode`, which can be used to determine the language the text should
            be translated to.

        Returns
        -------
        str
            The translated text which should be sent. This should not exceed ``500`` characters.

        Example
        -------

        .. code:: python3

            # For example purposes only the "translate" method is shown in this example...
            # The "get_langcode" method must also be implemented...

            class HelloTranslator(commands.Translator[str]):

                async def translate(self, ctx: commands.Context, text: str, langcode: str) -> str:
                    # Usually you would call an API, or retrieve from a database or dict or some other solution...
                    # This is just for an example...

                    if langcode == "en":
                        return text

                    elif langcode == "fr":
                        return "Bonjour!"

            @commands.command(name="hello", aliases=["bonjour"])
            @commands.translator(HelloTranslator)
            async def hello_command(ctx: commands.Context) -> None:
                await ctx.send_translated("Hello!")
        """
