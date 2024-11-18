from setuptools import setup  # type: ignore

from twitchio._version import _get_version


setup(version=_get_version(with_hash=False))
