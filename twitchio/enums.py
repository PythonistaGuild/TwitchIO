"""MIT License

Copyright (c) 2025 - Present Evie. P., Chillymosh and TwitchIO

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


__all__ = ("TwitchWSCloseCode",)


# fmt: off
class TwitchWSCloseCode(enum.IntEnum):
    INTERNAL_SERVER_ERROR = 4000  # Indicates a problem with the server (similar to an HTTP 500 status code).
    SENT_INBOUND_TRAFFIC  = 4001  # Sending outgoing messages to the server is prohibited with the exception of pong messages.
    PING_PONG_FAILED      = 4002  # You must respond to ping messages with a pong message. See Ping message.
    CONNECTION_UNUSED     = 4003  # When you connect to the server, you must create a subscription within 10 seconds or the connection is closed. The time limit is subject to change.
    RECONNECT_TIMEOUT     = 4004  # When you receive a session_reconnect message, you have 30 seconds to reconnect to the server and close the old connection. See Reconnect message.
    NETWORK_TIMEOUT       = 4005  # Transient network timeout.
    NETWORK_ERROR         = 4006  # Transient network error.
    INVALID_RECONNECT     = 4007  # The reconnect URL is invalid.

# fmt: on
