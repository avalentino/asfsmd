"""Unit tests for the asfsmd.core module."""

import netrc
import hashlib
import pathlib
import zipfile
from typing import List, Optional
from unittest import mock
from xml.etree import ElementTree as etree  # noqa: N813

import pytest

import asfsmd.core


def test_make_patterns_default():
    patterns = asfsmd.core.make_patterns()
    assert len(patterns) == 2
    assert "S1*.SAFE/manifest.safe" in patterns
    assert "S1*.SAFE/annotation/s1?-*-???-??-*.xml" in patterns


@pytest.mark.parametrize(
    "kwargs",
    [
        pytest.param(dict(beam="<beam>"), id="beam"),
        pytest.param(dict(pol="<pol>"), id="pol"),
    ],
)
def test_make_patterns(kwargs):
    patterns = asfsmd.core.make_patterns(**kwargs)

    assert len(patterns) == 2
    assert "S1*.SAFE/manifest.safe" in patterns

    value = next(iter(kwargs.values()))
    assert any([value in pattern for pattern in patterns])


@pytest.mark.parametrize(
    "kwargs",
    [
        pytest.param(dict(cal=True), id="cal"),
        pytest.param(dict(noise=True), id="noise"),
        pytest.param(dict(rfi=True), id="rfi"),
    ],
)
def test_make_patterns_extra(kwargs):
    patterns = asfsmd.core.make_patterns(**kwargs)

    assert len(patterns) == 3
    assert "S1*.SAFE/manifest.safe" in patterns
    assert "S1*.SAFE/annotation/s1?-*-???-??-*.xml" in patterns

    value = next(iter(kwargs.keys()))
    assert any([value in pattern for pattern in patterns])


def test_make_patterns_data():
    patterns = asfsmd.core.make_patterns(data=True)

    assert len(patterns) > 2
    assert "S1*.SAFE/manifest.safe" in patterns
    assert "S1*.SAFE/annotation/s1?-*-???-??-*.xml" in patterns

    assert any(["tiff" in pattern for pattern in patterns])
    assert any(["measurement" in pattern for pattern in patterns])


DEFAULT_PRODUCT = (
    "S1A_IW_SLC__1SDV_20230222T051014_20230222T051042_047344_05AECF_FDD1.SAFE"
)


class DummyProductWriter:
    DEFAULT_DATA_SIZE = 8 * 1024  # 4k

    def __init__(self, components: Optional[List[str]] = None):
        self._path: Optional[pathlib.Path] = None
        if components is None:
            components = [
                "./annotation/s1a-iw1-slc-vv-20230222t051014-20230222t051042-047344-05aecf-001.xml",  # noqa: E501
                "./annotation/s1a-iw2-slc-vv-20230222t051014-20230222t051042-047344-05aecf-002.xml",  # noqa: E501
                "./annotation/s1a-iw3-slc-vv-20230222t051014-20230222t051042-047344-05aecf-003.xml",  # noqa: E501
            ]
        self.components = {path: self.DEFAULT_DATA_SIZE for path in components}

    def _create_data_object(self, path: pathlib.Path, size: int):
        path.parent.mkdir(parents=True, exist_ok=True)
        data = path.name.encode("ascii")
        data = data + b"x" * (self.DEFAULT_DATA_SIZE - len(data))
        path.write_bytes(data)
        md5 = hashlib.md5(data)

        filename = str("." / path.relative_to(self._path))

        elem = etree.Element("dataObject")
        byte_stream_elem = etree.SubElement(
            elem, "byteStream", attrib=dict(size=str(size))
        )
        etree.SubElement(
            byte_stream_elem, "fileLocation", attrib=dict(href=filename)
        )
        checksum_elem = etree.SubElement(
            byte_stream_elem, "checksum", attrib=dict(checksumName="MD5")
        )
        checksum_elem.text = md5.hexdigest()

        return elem

    def _create_xmldoc(self):
        root = etree.Element("dummy_xfdu")
        data_object_section = etree.SubElement(root, "dataObjectSection")
        for path, size in self.components.items():
            assert self._path
            elem = self._create_data_object(self._path / path, size)
            data_object_section.append(elem)
        return etree.ElementTree(root)

    def write(self, path: pathlib.Path):
        try:
            self._path = path
            manifest_path = path / "manifest.safe"
            xmldoc = self._create_xmldoc()
            xmldoc.write(manifest_path)
        finally:
            self._path = None


def test__is_product_complete_complete(tmp_path):
    product_path = tmp_path.joinpath(DEFAULT_PRODUCT)
    writer = DummyProductWriter()
    writer.write(product_path)

    assert asfsmd.core._is_product_complete(product_path)


def test__is_product_complete_absent(tmp_path):
    product_path = tmp_path.joinpath(DEFAULT_PRODUCT)
    assert not asfsmd.core._is_product_complete(product_path)


def test__is_product_complete_missing_manifest(tmp_path):
    product_path = tmp_path.joinpath(DEFAULT_PRODUCT)
    writer = DummyProductWriter()
    writer.write(product_path)

    manifest_path = product_path / "manifest.safe"
    assert manifest_path.is_file()
    manifest_path.unlink()

    assert not asfsmd.core._is_product_complete(product_path)


def test__is_product_complete_missing_component(tmp_path):
    product_path = tmp_path.joinpath(DEFAULT_PRODUCT)
    writer = DummyProductWriter()
    writer.write(product_path)

    components = list(writer.components.keys())
    component_path = product_path.joinpath(components[-1])
    assert component_path.is_file()
    component_path.unlink()

    assert not asfsmd.core._is_product_complete(product_path)


def test__is_product_complete_incomplete_component(tmp_path):
    product_path = tmp_path.joinpath(DEFAULT_PRODUCT)
    writer = DummyProductWriter()
    writer.write(product_path)

    components = list(writer.components.keys())
    component_path = product_path.joinpath(components[-1])
    assert component_path.is_file()
    data = component_path.read_bytes()
    component_path.write_bytes(data[: len(data) // 2])

    assert not asfsmd.core._is_product_complete(product_path)


def test__is_product_complete_corrupted_component(tmp_path):
    product_path = tmp_path.joinpath(DEFAULT_PRODUCT)
    writer = DummyProductWriter()
    writer.write(product_path)

    components = list(writer.components.keys())
    component_path = product_path.joinpath(components[-1])
    assert component_path.is_file()
    data = component_path.read_bytes()
    assert b"s" in data
    data = data.replace(b"s", b"o")
    component_path.write_bytes(data)

    assert not asfsmd.core._is_product_complete(product_path)


class DummyZipFile:
    def __init__(self, filelist):
        self.filelist = filelist


def test__filter_components():
    filelist = [
        zipfile.ZipInfo(filename=""),
        zipfile.ZipInfo(filename="abc.txt"),
        zipfile.ZipInfo(filename="def.dat"),
    ]
    zf = DummyZipFile(filelist=filelist)

    patterns = ["*.txt"]
    out = asfsmd.core._filter_components(zf, patterns=patterns)
    assert len(out) == 1
    assert out == [filelist[1]]


class NummyNetrc(netrc.netrc):
    def __init__(self, file=None):
        super().__init__(file="dummy")


@mock.patch("netrc.netrc")
def test__get_auth(netrc):
    auth = asfsmd.core._get_auth("user", "password")
    assert isinstance(auth, asfsmd.core.Auth)
    assert auth == asfsmd.core.Auth("user", "password")


def test__get_auth_default(tmp_path):
    _netrc = netrc.netrc

    def fake_netrc(*args, **kewargx):
        data = """\
machine urs.earthdata.nasa.gov
    login user
    password password
"""
        netrc_path = tmp_path.joinpath("dummy_netrc")
        netrc_path.write_text(data)

        return _netrc(netrc_path)

    with mock.patch("netrc.netrc", new_callable=lambda: fake_netrc):
        auth = asfsmd.core._get_auth()
        assert isinstance(auth, asfsmd.core.Auth)
        assert auth == asfsmd.core.Auth("user", "password")


def test__get_auth_noauth(tmp_path):
    _netrc = netrc.netrc

    def fake_netrc(*args, **kewargx):
        netrc_path = tmp_path.joinpath("dummy_netrc")
        return _netrc(netrc_path)

    with mock.patch("netrc.netrc", new_callable=lambda: fake_netrc):
        with pytest.raises(FileNotFoundError):
            asfsmd.core._get_auth()
