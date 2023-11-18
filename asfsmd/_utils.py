"""Utility functions for asfsmd."""

from typing import Any, Iterable, List


def unique(data: Iterable[Any]) -> List[Any]:
    """Return a list of unique items preserving the input ordering."""
    unique_items = []
    unique_items_set = set()
    for item in data:
        if item not in unique_items_set:
            unique_items.append(item)
            unique_items_set.add(item)
    return unique_items
