from dataclasses import is_dataclass
from types import MappingProxyType

import frozendict


def deep_freeze(obj):
    """
    Recursively freeze mutable structures:
    - list -> tuple
    - dict -> frozendict
    - set -> frozenset
    """
    if is_dataclass(obj):
        return obj
    elif isinstance(obj, dict):
        return frozendict.frozendict(
            {deep_freeze(k): deep_freeze(v) for k, v in obj.items()}
        )
    elif isinstance(obj, list):
        return tuple(deep_freeze(x) for x in obj)
    elif isinstance(obj, set):
        return frozenset(deep_freeze(x) for x in obj)
    elif isinstance(obj, tuple):
        return tuple(deep_freeze(x) for x in obj)
    else:
        return obj
