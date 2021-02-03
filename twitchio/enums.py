import enum

__all__ = (
    "PredictionEnum",
    "BroadcasterTypeEnum",
    "UserTypeEnum",
    "ModEventEnum"
)

class PredictionEnum(enum.Enum):
    blue_1 = "blue-1"
    pink_2 = "pink-2"

class BroadcasterTypeEnum(enum.Enum):
    partner = "partner"
    affilate = "affilate"
    none = ""

class UserTypeEnum(enum.Enum):
    staff = "staff"
    admin = "admin"
    global_mod = "global_mod"
    none = ""

class ModEventEnum(enum.Enum):
    moderator_remove = "moderation.moderator.remove"
    moderator_add    = "moderation.moderator.add"