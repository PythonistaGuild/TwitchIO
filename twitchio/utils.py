import json


try:
    import orjson  # type: ignore

    _from_json = orjson.loads  # type: ignore
except ImportError:
    _from_json = json.loads


__all__ = ("_from_json",)
