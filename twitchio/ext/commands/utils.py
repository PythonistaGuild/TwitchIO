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

from typing import Any, TypeVar, Optional

K = TypeVar("K", bound=str)
V = TypeVar("V")


class _CaseInsensitiveDict(dict):
    def __getitem__(self, key: K) -> V:
        return super().__getitem__(key.lower())

    def __setitem__(self, key: K, value: V) -> None:
        super().__setitem__(key.lower(), value)

    def __delitem__(self, key: K) -> None:
        return super().__delitem__(key.lower())

    def __contains__(self, key: K) -> bool:  # type: ignore
        return super().__contains__(key.lower())

    def get(self, key: K, default: Any = None) -> Optional[V]:
        return super().get(key, default)

    def pop(self, key: K, default: Any = None) -> V:
        return super().pop(key, default)
