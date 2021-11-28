import argparse
import re


parser = argparse.ArgumentParser()
parser.add_argument("--latest")
args = parser.parse_args()


with open("../../twitchio/__init__.py", "r+") as fp:
    data = fp.read()

    data = re.sub(r"__version__ = \"\d+.\d+.\d+\"", f'__version__ = "{args.latest.removeprefix("v")}"', data)

    fp.seek(0)
    fp.write(data)
