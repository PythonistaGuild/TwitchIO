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

import logging

from ..utils import ColorFormatter
from .aio_adapter import AiohttpAdapter as AiohttpAdapter


handler = logging.StreamHandler()
handler.setFormatter(ColorFormatter())
logger = logging.getLogger(__name__)
logger.addHandler(handler)


try:
    from .starlette_adapter import StarletteAdapter as StarletteAdapter
except ImportError:
    msg = "Please install the required packages: 'pip install twitchio[starlette]' to use the StarletteAdapter."
    logger.warning("Starlette or uvicorn is not installed, StarletteAdapter will not be available. %s", msg)


logger.removeHandler(handler)
