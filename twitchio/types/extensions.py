from typing import Dict, Literal, TypedDict

from typing_extensions import NotRequired


class Extension(TypedDict):
    active: Literal[True, False]
    id: str
    version: str
    x: NotRequired[int]
    y: NotRequired[int]


class ExtensionBuilder(TypedDict):
    panel: Dict[str, Extension]
    overlay: Dict[str, Extension]
    component: Dict[str, Extension]
