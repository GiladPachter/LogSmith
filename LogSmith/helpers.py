from typing import Iterable


def contains_any(s: str, subs: Iterable[str]):
    for sub in subs:
        if sub in s:
            return True
    return False


def contains_all(s: str, subs: Iterable[str]):
    for sub in subs:
        if sub not in s:
            return False
    return True
