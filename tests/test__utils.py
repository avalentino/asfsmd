"""Unit tests for the `asfsmd._utils` module."""

import itertools

import pytest

from asfsmd._utils import unique


@pytest.mark.parametrize(
    ["in_", "out"],
    [
        pytest.param(["a", "b", "c"], ["a", "b", "c"], id="unique-list"),
        pytest.param(["a", "b", "c", "b"], ["a", "b", "c"], id="list"),
        pytest.param((1, 2, 2, 3, 1, 2), [1, 2, 3], id="tuple"),
        pytest.param(range(3), [0, 1, 2], id="generator"),
        pytest.param(
            itertools.chain(range(3, 0, -1), range(3)),
            [3, 2, 1, 0],
            id="reversed-generator",
        ),
    ],
)
def test_unique(in_, out):
    assert unique(in_) == out
