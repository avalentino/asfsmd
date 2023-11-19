"""Unit tests for the asfsmd.cli module."""

import pathlib
from unittest import mock

import pytest

import asfsmd.core
from asfsmd.cli import _load_product_lists, asfsmd_cli


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
    data = _load_product_lists(jsonfile)
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
    data = _load_product_lists(textfile)
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
    data = _load_product_lists(jsonfile, textfile)
    assert data == odata


dummy_auth = asfsmd.core.Auth("user", "password")


@mock.patch("asfsmd.cli._get_auth", mock.Mock(return_value=dummy_auth))
@mock.patch("asfsmd.cli.download_components_from_urls", mock.Mock())
@mock.patch("asfsmd.cli.download_annotations")
def test_asfsmd_cli_productlist(download_annotations):
    product_list = ["product01", "product02"]
    asfsmd_cli(product_list, noprogress=True)
    download_annotations.assert_called_once_with(
        product_list,
        outdir=pathlib.Path("."),
        auth=dummy_auth,
        patterns=asfsmd.core.make_patterns(),
        block_size=asfsmd.core.BLOCKSIZE,
        noprogress=True,
    )


@mock.patch("asfsmd.cli._get_auth", mock.Mock(return_value=dummy_auth))
@mock.patch("asfsmd.cli.download_components_from_urls", mock.Mock())
@mock.patch("asfsmd.cli.download_annotations")
def test_asfsmd_cli_filelist(download_annotations, tmp_path):
    product_list = ["product01", "product02"]
    filelist = tmp_path.joinpath("filelist.txt")
    filelist.write_text("\n".join(product_list))
    asfsmd_cli([filelist], file_list=True, noprogress=True)
    download_annotations.assert_called_once_with(
        product_list,
        outdir=pathlib.Path("."),
        auth=dummy_auth,
        patterns=asfsmd.core.make_patterns(),
        block_size=asfsmd.core.BLOCKSIZE,
        noprogress=True,
    )


@mock.patch("asfsmd.cli._get_auth", mock.Mock(return_value=dummy_auth))
@mock.patch("asfsmd.cli.download_annotations", mock.Mock())
@mock.patch("asfsmd.cli.download_components_from_urls")
def test_asfsmd_cli_urls(download_components_from_urls):
    urls = ["url1", "url2"]
    asfsmd_cli(urls, urls=True, noprogress=True)
    download_components_from_urls.assert_called_once_with(
        urls,
        outdir=pathlib.Path("."),
        auth=dummy_auth,
        patterns=asfsmd.core.make_patterns(),
        block_size=asfsmd.core.BLOCKSIZE,
        noprogress=True,
    )
