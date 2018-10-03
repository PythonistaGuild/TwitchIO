from setuptools import setup
import re, os

on_rtd = os.getenv('READTHEDOCS') == 'True'

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

if on_rtd:
    requirements.append('sphinx==1.7.4')
    requirements.append('sphinxcontrib-napoleon')
    requirements.append('sphinxcontrib-asyncio')
    requirements.append('sphinxcontrib-websupport')
    requirements.append('Pygments')

version = ''
with open('twitchio/__init__.py') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('version is not set')

# Thanks Dannyo(Rapptz) again...
if version.endswith(('a', 'b', 'rc')):
    # append version identifier based on commit count
    try:
        import subprocess
        p = subprocess.Popen(['git', 'rev-list', '--count', 'HEAD'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if out:
            version += out.decode('utf-8').strip()
        p = subprocess.Popen(['git', 'rev-parse', '--short', 'HEAD'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if out:
            version += '+' + out.decode('utf-8').strip()
    except Exception:
        pass

if not version:
    raise RuntimeError('version is not set')

readme = ''
with open('README.rst') as f:
    readme = f.read()

setup(name='twitchio',
      author='EvieePy',
      url='https://github.com/EvieePy/TwitchIO',
      version=version,
      packages=['twitchio', 'twitchio.ext.commands'],
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
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
      ]
)
