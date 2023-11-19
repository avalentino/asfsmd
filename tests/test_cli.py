"""Unit tests for the asfsmd.cli module."""

import pathlib
from unittest import mock

import asfsmd.core
from asfsmd.cli import asfsmd_cli

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
