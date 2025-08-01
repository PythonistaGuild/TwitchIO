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
import asyncio
import getpass
import os
import pathlib
import platform
import re
import subprocess
import sys
from collections.abc import Callable

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

new_bot = parser.add_argument_group("Create Bot", "Create and generate bot boilerplate via an interactive walkthrough.")
new_bot.add_argument("--create-new", action="store_true", help="Start an interactive walkthrough.")

args = parser.parse_args()


COMPONENT = """from __future__ import annotations

from typing import TYPE_CHECKING

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

MAIN = """import asyncio
import logging
import tomllib

from bot import Bot

import twitchio


LOGGER: logging.Logger = logging.getLogger(__name__)


def main() -> None:
    twitchio.utils.setup_logging(level=logging.INFO)

    with open("config.toml", "rb") as fp:
        config = tomllib.load(fp)

    async def runner() -> None:
        async with Bot(**config["bot"]) as bot:
            await bot.start()

    try:
        asyncio.run(runner())
    except KeyboardInterrupt:
        LOGGER.warning("Shutting down due to Keyboard Interrupt.")


if __name__ == "__main__":
    main()

"""

BOT = """from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from twitchio import eventsub
from twitchio.ext import commands


if TYPE_CHECKING:
    from twitchio.authentication import UserTokenPayload


LOGGER: logging.Logger = logging.getLogger("Bot")


class Bot(commands.AutoBot):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    async def setup_hook(self) -> None:
        subs: list[eventsub.SubscriptionPayload] = []

        with open(".tio.tokens.json", "rb") as fp:
            tokens = json.load(fp)

            for user_id in tokens:
                if user_id == self.user.id:
                    continue

                subs.extend(self.generate_subs(user_id))

        if subs:
            await self.multi_subscribe(subs)

        {COMP}

    async def event_ready(self) -> None:
        LOGGER.info("Logged in as: %s. Owner: %s", self.user, self.owner)

    def generate_subs(self, user_id: str) -> tuple[eventsub.SubscriptionPayload, ...]:
        # Add the required eventsub subscriptions for each user...
        assert self.user

        return (eventsub.ChatMessageSubscription(broadcaster_user_id=user_id, user_id=self.user.id),)

    async def event_oauth_authorized(self, payload: UserTokenPayload) -> None:
        await self.add_token(payload.access_token, payload.refresh_token)

        if not payload.user_id:
            return

        if payload.user_id == self.bot_id:
            # Don't subscribe to events for the bot user
            return

        await self.multi_subscribe(self.generate_subs(payload.user_id))

"""

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
    package = "twitchio[starlette]" if starlette else "twitchio"
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

    starlette = bool_check(
        validate_input(
            "Would you like to install the optional Starlette and Uvicorn packages? (y/N): ",
            bool_validate,
        )
    )
    install_packages(exe, starlette)


async def generate_bot() -> None:
    name = validate_input("Project name? (Leave blank to generate files in this directory): ")
    if name:
        _dir = pathlib.Path(name)
        _dir.mkdir(exist_ok=True)
        os.chdir(_dir)
    else:
        _dir = pathlib.Path.cwd()

    if sys.prefix != sys.base_prefix:
        resp = bool_check(
            validate_input(
                "No virtual environment used. Would you like to create one? (y/N): ",
                bool_validate,
            )
        )

        if resp:
            generate_venv()

    components = bool_check(validate_input("\nWould you like to setup commands.Components? (y/N): ", bool_validate))
    if components:
        comp_dir = pathlib.Path("components")
        comp_dir.mkdir(exist_ok=True)

        with open(comp_dir / "general.py", "w") as fp:
            fp.write(COMPONENT)

    while True:
        client_id = validate_input("Please enter your Client-ID: ")
        cid_reenter = validate_input("Please re-enter your Client-ID: ")

        if client_id != cid_reenter:
            print("Client-ID does not match, please try again...", end="\n\n")
            continue

        break

    while True:
        client_sec = getpass.getpass("Please enter your Client-Secret: ")
        csec_reenter = getpass.getpass("Please re-enter your Client-Secret: ")

        if client_sec != csec_reenter:
            print("Client-Secret does not match, please try again...", end="\n\n")
            continue

        break

    while True:
        owner_name = validate_input("Please enter the Twitch username of the owner of this Bot (E.g. chillymosh): ")
        bot_name = validate_input("Please enter the Twitch username of the Bot Account (E.g. chillybot): ")
        names = f"Owner Name: '{owner_name}'\nBot Name: '{bot_name}'"

        correct = bool_check(validate_input(f"Is this information correct? (y/N)\n\n{names}\n", bool_validate))
        if not correct:
            continue

        break

    import twitchio

    client = twitchio.Client(client_id=client_id, client_secret=client_sec)
    async with client:
        await client.login()

        owner = bot = None
        try:
            owner, bot = await client.fetch_users(logins=[owner_name, bot_name])
        except twitchio.HTTPException:
            print(
                "Error fetching IDs of provided users. Please do this manually and enter them into the generated config.toml"
            )

    prefixr = validate_input("Please enter a command prefix for the Bot (Leave blank for '!'): ")
    prefix = prefixr or "!"

    config_data = (
        f'[bot]\nclient_id = "{client_id}"\nclient_secret = "{client_sec}"\n'
        f'owner_id = "{owner.id if owner else ""}"\nbot_id = "{bot.id if bot else ""}"\n'
        f'prefix = "{prefix}"'
    )

    with open("config.toml", "w") as fp:
        fp.write(config_data)

    with open("main.py", "w") as fp:
        fp.write(MAIN)

    with open("bot.py", "w") as fp:
        comp = 'await self.load_module("components.general")' if components else ""
        fp.write(BOT.format(COMP=comp))

    print("\n\nSuccessfully created Bot boilerplate with the provided details!")


if args.version:
    version_info()

elif args.create_new:
    asyncio.run(generate_bot())
