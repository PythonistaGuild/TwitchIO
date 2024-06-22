# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2017-present TwitchIO

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""
from __future__ import annotations
from typing import Dict


class StringParser:
    def __init__(self):
        self.count = 0
        self.index = 0
        self.eof = 0
        self.start = 0
        self.words: Dict[int, str] = {}
        self.ignore = False

    def process_string(self, msg: str) -> Dict[int, str]:
        while self.count < len(msg):
            loc = msg[self.count]

            if loc == '"' and not self.ignore:
                self.ignore = True
                self.start = self.count + 1

            elif loc == '"' and self.ignore:
                self.words[self.index] = msg[self.start : self.count]
                self.index += 1
                self.ignore = False
                self.start = self.count + 1

            elif loc.isspace() and not self.ignore:
                if self.start != self.count:
                    self.words[self.index] = msg[self.start : self.count]
                    self.index += 1

                self.start = self.count + 1

            self.count += 1

        if self.start < len(msg) and not self.ignore:
            self.words[self.index] = msg[self.start : len(msg)].strip()

        return self.words

    def copy(self) -> StringParser:
        new = self.__class__()
        new.count = self.count
        new.start = self.start
        new.words = self.words.copy()
        new.index = self.index
        new.ignore = self.ignore
        return new
