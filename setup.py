import re

from setuptools import setup  # type: ignore


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
        except Exception:
            pass

    return version


setup(version=get_version())
