"""
MIT License

Copyright (c) 2017 - Present PythonistaGuild

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

import enum


__all__ = ("DeviceCodeRejection",)


class DeviceCodeRejection(enum.Enum):
    """An enum respresenting the reason a DCF (Device Code Flow) failed.

    Attributes
    ----------
    UNKNOWN
        The reason is unknown. Twitch likely did not provide one or the exception was a 5xx status code.
    INVALID_REFRESH_TOKEN
        The refresh used was invalid or expired. DCF refresh tokens can only be used once and last ``30`` days.
    INVALID_DEVICE_CODE
        The provided device code was not valid or the user has already authenticated with this code.
    """

    UNKNOWN = "unknown"
    INVALID_REFRESH_TOKEN = "invalid refresh token"
    INVALID_DEVICE_CODE = "invalid device code"
