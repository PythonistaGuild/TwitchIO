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

__title__ = "TwitchIO"
__author__ = "PythonistaGuild"
__license__ = "MIT"
__copyright__ = "Copyright 2017-Present (c) TwitchIO, PythonistaGuild"
__version__ = "3.1.0"

from . import (  # noqa: F401
    authentication as authentication,
    eventsub as eventsub,
    types_ as types,  # pyright: ignore [reportUnusedImport]
    utils as utils,
    web as web,
)
from .assets import Asset as Asset
from .authentication import Scopes as Scopes
from .client import *
from .exceptions import *
from .http import HTTPAsyncIterator as HTTPAsyncIterator, Route as Route
from .models import *
from .payloads import *
from .user import *
from .utils import Color as Color, Colour as Colour
