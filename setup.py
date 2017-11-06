from setuptools import setup
import re, os

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

version = ''
with open('twitchio/__init__.py') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('version is not set')

readme = ''
with open('README.rst') as f:
    readme = f.read()

setup(name='twitchio',
      author='MysterialPy',
      url='https://github.com/MysterialPy/TwitchIO',
      version=version,
      packages=['twitchio', 'twitchio.commands'],
      license='MIT',
      description='A python IRC and API wrapper for Twitch.',
      long_description=readme,
      include_package_data=True,
      install_requires=requirements,
      classifiers=[
        'Development Status :: 2 - Beta',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
      ]
)