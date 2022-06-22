"""MIT License

Copyright (c) 2017-2022 TwitchIO

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

import datetime
import iso8601
from typing import Any, Union, Dict, List

__all__ = ("json_loader", "json_dumper")

try:
    from orjson import loads as _loads, dumps as _orjson_dumps
    def _dumps(obj: Union[Dict[str, Any], List[Any]]) -> str: # orjson returns bytes instead of str, so patch it here
        return _orjson_dumps(obj).decode()

    HAS_MODDED_JSON = True
except ModuleNotFoundError:
    try:
        from ujson import loads as _loads, dumps as _dumps
        HAS_MODDED_JSON = True
    except ModuleNotFoundError:
        from json import loads as _loads, dumps as _dumps
        HAS_MODDED_JSON = False

json_loader = _loads
json_dumper = _dumps

MISSING: Any = object()

def parse_timestamp(timestamp: str) -> datetime.datetime:
    """

    Parameters
    ----------
    timestamp: :class:`str`
        The timestamp to be parsed, in an iso8601 format.

    Returns
    -------
    :class:`datetime.datetime`
        The parsed timestamp.

    """
    return iso8601.parse_date(timestamp, datetime.timezone.utc)
