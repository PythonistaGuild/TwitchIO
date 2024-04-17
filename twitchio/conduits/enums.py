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


class TransportMethod(enum.Enum):
    WEBHOOK = "webhook"
    WEBSOCKET = "websocket"


class ShardStatus(enum.Enum):
    ENABLED = "enabled"
    WEBHOOK_VERIFICATION_PENDING = "webhook_callback_verification_pending"
    WEBHOOK_VERIFICATION_FAILED = "webhook_callback_verification_failed"
    NOTIFICATION_FAILURES_EXCEEDED = "notification_failures_exceeded"
    WEBSOCKET_DISCONNECTED = "websocket_disconnected"
    WEBSOCKET_FAILIED_PING = "websocket_failed_ping_pong"
    WEBSOCKET_RECEIVED_INBOUD = "websocket_received_inbound_traffic"
    WEBSOCKET_INTERNAL_ERROR = "websocket_internal_error"
    WEBSOCKET_NETWORK_TIMEOUT = "websocket_network_timeout"
    WEBSOCKET_NETWORK_ERROR = "websocket_network_error"
    WEBSOCKET_FAILED_RECONNECT = "websocket_failed_to_reconnect"


class CloseCode(enum.Enum):
    INTERNAL_SERVER_ERROR = 4000
    SENT_INBOUND_TRAFFIC = 4001
    FAILED_PING = 4002
    CONNECTION_UNUSED = 4003
    RECONNECT_GRACE_TIMEOUT = 4004
    NETWORK_TIMEOUT = 4005
    NETWORK_ERROR = 4006
    INVALID_RECONNECT = 4007


class MessageType(enum.Enum):
    SESSION_WELCOME = "session_welcome"
    SESSION_KEEPALIVE = "session_keepalive"
    NOTIFICATION = "notification"
    SESSION_RECONNECT = "session_reconnect"
    REVOCATION = "revocation"
