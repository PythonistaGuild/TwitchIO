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

import argparse
import platform
import sys

import aiohttp

from ._version import _get_version


try:
    import starlette

    starlette_version = starlette.__version__
except ImportError:
    starlette_version = "Not Installed/Not Found"

try:
    import uvicorn

    uvicorn_version = uvicorn.__version__
except ImportError:
    uvicorn_version = "Not Installed/Not Found"


parser = argparse.ArgumentParser(prog="twitchio")
parser.add_argument("--version", action="store_true", help="Get version and debug information for TwitchIO.")

args = parser.parse_args()


def version_info() -> None:
    python_info = "\n".join(sys.version.split("\n"))

    info: str = f"""
    twitchio : {_get_version()}
    aiohttp  : {aiohttp.__version__}

    Python:
        - {python_info}
    System:
        - {platform.platform()}
    Extras:
        - Starlette : {starlette_version}
        - Uvicorn   : {uvicorn_version}
    """

    print(info)


if args.version:
    version_info()
