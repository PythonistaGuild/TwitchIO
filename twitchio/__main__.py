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
import os
import pathlib
import platform
import re
import sys
import subprocess
from typing import Callable

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

# TODO: Only uncomment for testing, until complete...
# new_bot = parser.add_argument_group("Create Bot", "Create and generate bot boilerplate via an interactive walkthrough.")
# new_bot.add_argument("--create-new", action="store_true", help="Start an interactive walkthrough.")

args = parser.parse_args()


COMPONENT = """from typing import TYPE_CHECKING

import twitchio
from twitchio.ext import commands


if TYPE_CHECKING:
    from ..bot import Bot


class GeneralComponent(commands.Component):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @commands.command()
    async def hi(self, ctx: commands.Context) -> None:
        await ctx.send(f"Hello {ctx.author.mention}")


async def setup(bot: Bot) -> None:
    await bot.add_component(GeneralComponent(bot))


# This is an optional teardown coroutine for miscellaneous clean-up if necessary.
async def teardown(bot: Bot) -> None: ...

"""

MAIN = """"""

BOOLS = {
    "y": True, 
    "yes": True,
    "n": False,
    "no": False,
    "t": True,
    "true": True,
    "f": False,
    "false": False,
    "1": True,
    "0": False,
}


def bool_check(inp: str) -> bool | None:
    return BOOLS.get(inp.lower())


def bool_validate(inp: str) -> bool:
    return BOOLS.get(inp.lower()) is not None


def validate_input(inp: str, check: Callable[[str], bool] | None = None, *, error_msg: str | None = None) -> str:
    error_msg = error_msg or "Invalid input, please try again!"
    
    while True:
        response = input(inp)
        if not check:
            break
        
        try:
            result = check(response)
        except Exception:
            result = False
        
        if result is False:
            print(error_msg, end="\n\n")
            continue
        
        break
    
    return response


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


def install_packages(exe: pathlib.Path, starlette: bool | None = False) -> None:
    package = "twitchio" if not starlette else "twitchio[starlette]"
    subprocess.call([exe, "-m", "pip", "install", package, "--upgrade", "--no-cache"])


def generate_venv() -> None:
    # Create the venv...
    subprocess.call([sys.executable, "-m", "venv", ".venv"])
    
    system = platform.system()
    
    if system == "Windows":
        exe = pathlib.Path(".venv") / "Scripts" / "python.exe"
    elif system in ["Darwin", "Linux"]:
        exe = pathlib.Path(".venv") / "bin" / "python"
    else:        
        print("Unsupported operating system... Skipping package installation. Please manually install required packages.")
        return
    
    starlette = bool_check(validate_input("Would you like to install the optional Starlette and Uvicorn packages? (y/N): ",  bool_validate,))
    install_packages(exe, starlette)  


def generate_bot() -> ...:
    name = validate_input("Project name? (Leave blank to generate files in this directory): ")
    if name:
        dir = pathlib.Path(name)
        dir.mkdir(exist_ok=True)
        os.chdir(dir)
    else:
        dir = pathlib.Path.cwd()
    
    if sys.prefix != sys.base_prefix:
        resp = bool_check(validate_input("No virtual environment used. Would you like to create one? (y/N): ",  bool_validate,))
        
        if resp:
            generate_venv()
    
    components = bool_check(validate_input("Would you like to setup commands.Components? (y/N): ",  bool_validate))
    if components:
        comp_dir = pathlib.Path("components")
        comp_dir.mkdir(exist_ok=True)
        
        with open(comp_dir / "general.py", "w") as fp:
            fp.write(COMPONENT)
    
    # TODO: .env
    # TODO: client details
    # TODO: fetch owner/bot IDs
    # with open(dir / "main.py", "w") as fp:
    #     ...
        
    # with open(dir / "bot.py", "w") as fp:
    #     ...


if args.version:
    version_info()

elif args.create_new:
    generate_bot()
