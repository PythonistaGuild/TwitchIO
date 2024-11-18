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
import re
import sys

import aiohttp


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


def get_version() -> str:
    version = ""
    with open("twitchio/__init__.py") as f:
        match = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE)

    if not match or not match.group(1):
        raise RuntimeError("Version is not set")

    version = match.group(1)

    if version.endswith(("dev", "a", "b", "rc")):
        # append version identifier based on commit count
        try:
            import subprocess

            p = subprocess.Popen(["git", "rev-list", "--count", "HEAD"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, _ = p.communicate()
            if out:
                version += out.decode("utf-8").strip()
            p = subprocess.Popen(["git", "rev-parse", "--short", "HEAD"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, _ = p.communicate()
            if out:
                version += "+g" + out.decode("utf-8").strip()
        except Exception:
            pass

    return version


def version_info() -> None:
    python_info = "\n".join(sys.version.split("\n"))

    info: str = f"""
    twitchio : {get_version()}
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
