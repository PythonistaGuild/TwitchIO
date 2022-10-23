"""MIT License

Copyright (c) 2017-present TwitchIO

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
import collections
from typing import Optional


class Cache:
    def __init__(self, *, size: Optional[int] = None):
        self.size = size or 99999999  # Arbitrarily large size...

        self.nodes = collections.OrderedDict()

    def __str__(self):
        return str(self.nodes)

    def __setitem__(self, key, value):
        if key in self.nodes:
            self.nodes.move_to_end(key, last=False)
            self.nodes[key] = value

            return

        if self.size == len(self.nodes):
            self.nodes.popitem(last=True)

        self.nodes[key] = value
        self.nodes.move_to_end(key, last=False)

    def __getitem__(self, item):
        value = self.nodes[item]

        self.nodes.move_to_end(item, last=False)
        return value

    def __contains__(self, item):
        return item in self.nodes

    def __delitem__(self, key):
        self.nodes.pop(key, None)

    def get(self, key, *, default=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default

    def pop(self, key, *, default=None):
        return self.nodes.pop(key, default)

    def keys(self):
        return self.nodes.keys()

    def values(self):
        return self.nodes.values()

    def items(self):
        return self.nodes.items()
