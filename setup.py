import re

from setuptools import setup


def get_version() -> str:
    version = ""
    with open("twitchio/__init__.py") as f:
        version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

    if version.endswith(("dev", "a", "b", "rc")):
        # append version identifier based on commit count
        try:
            import subprocess

            p = subprocess.Popen(["git", "rev-list", "--count", "HEAD"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
            if out:
                version += out.decode("utf-8").strip()
            p = subprocess.Popen(
                ["git", "rev-parse", "--short", "HEAD"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            out, err = p.communicate()
            if out:
                version += "+g" + out.decode("utf-8").strip()
        except Exception:
            pass

    return version


setup(version=get_version())
