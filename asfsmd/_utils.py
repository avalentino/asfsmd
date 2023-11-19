"""Utility functions for asfsmd."""

import json
import pathlib
import collections
from typing import Any, Dict, Iterable, List

from .common import PathType


def unique(data: Iterable[Any]) -> List[Any]:
    """Return a list of unique items preserving the input ordering."""
    unique_items = []
    unique_items_set = set()
    for item in data:
        if item not in unique_items_set:
            unique_items.append(item)
            unique_items_set.add(item)
    return unique_items


def load_product_lists(*filenames: PathType) -> Dict[str, List[str]]:
    """Load product list form files."""
    data: Dict[str, List[str]] = collections.defaultdict(list)
    for filename in filenames:
        filename = pathlib.Path(filename)
        if filename.suffix == ".json":
            data.update(json.loads(filename.read_text()))
        else:
            with filename.open() as fd:
                for line in fd:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    data[""].append(line)

    # Strip .zip or .SAFE extensions
    return {
        key: unique(
            item.replace(".zip", "").replace(".SAFE", "") for item in values
        )
        for key, values in data.items()
    }
