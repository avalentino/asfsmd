"""Unit tests for the `asfsmd._utils` module."""

import itertools

import pytest

from asfsmd._utils import unique, load_product_lists


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


@pytest.mark.parametrize(
    ["idata", "odata"],
    [
        pytest.param(
            """\
{
    "": [
        "filelist01.txt",
        "filelist02.txt"
    ],
    "a": [
        "a01.txt",
        "a02.txt"
    ],
    "b/1": [
        "b01.txt",
        "b02.txt"
    ]
}
""",
            {
                "": ["filelist01.txt", "filelist02.txt"],
                "a": ["a01.txt", "a02.txt"],
                "b/1": ["b01.txt", "b02.txt"],
            },
            id="unique",
        ),
        pytest.param(
            """\
{
    "": [
        "filelist01.txt",
        "filelist02.txt",
        "a02.txt"
    ],
    "a": [
        "a01.txt",
        "a02.txt"
    ],
    "b/1": [
        "b01.txt",
        "b02.txt"
    ]
}
""",
            {
                "": ["filelist01.txt", "filelist02.txt", "a02.txt"],
                "a": ["a01.txt", "a02.txt"],
                "b/1": ["b01.txt", "b02.txt"],
            },
            id="unique-per-section",
        ),
        pytest.param(
            """\
{
    "": [
        "filelist01.txt",
        "filelist02.txt",
        "filelist01.txt"
    ],
    "a": [
        "a01.txt",
        "a02.txt",
        "a02.txt"
    ],
    "b/1": [
        "b01.txt",
        "b02.txt"
    ]
}
""",
            {
                "": ["filelist01.txt", "filelist02.txt"],
                "a": ["a01.txt", "a02.txt"],
                "b/1": ["b01.txt", "b02.txt"],
            },
            id="duplicate",
        ),
    ],
)
def test__load_product_lists_json(idata, odata, tmp_path):
    jsonfile = tmp_path / "productlist.json"
    jsonfile.write_text(idata)
    data = load_product_lists(jsonfile)
    assert data == odata


@pytest.mark.parametrize(
    ["idata", "odata"],
    [
        pytest.param(
            """\
filelist01.txt
filelist02.txt
filelist03.txt
""",
            {
                "": ["filelist01.txt", "filelist02.txt", "filelist03.txt"],
            },
            id="unique",
        ),
        pytest.param(
            """\
# comment line
filelist01.txt
filelist02.txt
  # indented comment line
  filelist03.txt
""",
            {
                "": ["filelist01.txt", "filelist02.txt", "filelist03.txt"],
            },
            id="unique-with-comment",
        ),
        pytest.param(
            # NOTE: filename01.txt has trailing spaces
            (
                "filelist01.txt  \n"
                "\n"
                "filelist02.txt\n"
                "  \n"
                "  filelist03.txt  \n"
            ),
            {
                "": ["filelist01.txt", "filelist02.txt", "filelist03.txt"],
            },
            id="unique-with-emply-line",
        ),
        pytest.param(
            """\
filelist01.txt
filelist02.txt
filelist03.txt
filelist03.txt
""",
            {
                "": ["filelist01.txt", "filelist02.txt", "filelist03.txt"],
            },
            id="duplicate",
        ),
        pytest.param(
            """\
# comment
filelist01.txt
filelist02.txt

  # duplicates
  filelist03.txt
  filelist03.txt
""",
            {
                "": ["filelist01.txt", "filelist02.txt", "filelist03.txt"],
            },
            id="duplicate-with-comments-and-empty-lines",
        ),
    ],
)
def test__load_product_lists_text(idata, odata, tmp_path):
    textfile = tmp_path / "productlist.txt"
    textfile.write_text(idata)
    data = load_product_lists(textfile)
    assert data == odata


@pytest.mark.parametrize(
    ["jsondata", "textdata", "odata"],
    [
        pytest.param(
            """\
{
  "a": [
    "a01.txt",
    "a02.txt"
  ],
  "b/1": [
    "b01.txt",
    "b02.txt"
  ]
}
""",
            """\
filelist01.txt
filelist02.txt
""",
            {
                "": [
                    "filelist01.txt",
                    "filelist02.txt",
                ],
                "a": [
                    "a01.txt",
                    "a02.txt",
                ],
                "b/1": [
                    "b01.txt",
                    "b02.txt",
                ],
            },
            id="unique",
        ),
        pytest.param(
            """\
{
  "": [
    "filelist01.txt",
    "filelist02.txt"
  ],
  "a": [
    "a01.txt",
    "a02.txt"
  ]
}
""",
            """\
filelist01.txt
filelist02.txt
filelist03.txt
""",
            {
                "": [
                    "filelist01.txt",
                    "filelist02.txt",
                    "filelist03.txt",
                ],
                "a": [
                    "a01.txt",
                    "a02.txt",
                ],
            },
            id="duplicate",
        ),
    ],
)
def test__load_product_lists_multifile(jsondata, textdata, odata, tmp_path):
    jsonfile = tmp_path / "jsonfile.json"
    jsonfile.write_text(jsondata)
    textfile = tmp_path / "textfile.txt"
    textfile.write_text(textdata)
    data = load_product_lists(jsonfile, textfile)
    assert data == odata
