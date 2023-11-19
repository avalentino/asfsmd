"""Core functions for the ASF Sentinel-1 Metadata Download tool."""

import os
import netrc
import fnmatch
import hashlib
import logging
import pathlib
import zipfile
import warnings
import functools
import importlib
from typing import List, Optional
from xml.etree import ElementTree as etree  # noqa: N813
from urllib.parse import urlparse

import tqdm
import asf_search as asf

from .common import Auth, BLOCKSIZE, PathType, Url

__all__ = [
    "download_annotations",
    "download_components_from_urls",
    "make_patterns",
]


_log = logging.getLogger(__name__)


def _get_client_type():
    implementations = ["httpio", "fsspec", "remotezip"]
    if os.environ.get("ASFSMD_CLIENT") in implementations:
        name = os.environ.get("ASFSMD_CLIENT")
        name = f".{name}_client"
        mod = importlib.import_module(name, package=__package__)
    else:
        for name in implementations:
            name = f".{name}_client"
            try:
                mod = importlib.import_module(name, package=__package__)
                break
            except ImportError:
                _log.debug("exception caught:", exc_info=True)
                pass
        else:
            raise ImportError(
                f"Unable to import any of the asfsmd client implementations. "
                f"At least one of the following modules is required: "
                f"{','.join(map(repr, implementations))}"
            )

    _log.debug(f"Client: {mod.Client}")
    return mod.Client


_ClientType = _get_client_type()


def query(products):
    """Query the specified Sentinel-1 products."""
    if isinstance(products, str):
        products = [products]
    results = asf.granule_search(products)
    results = [
        result
        for result in results
        if "METADATA" not in result.properties["processingLevel"]
    ]
    return results


def make_patterns(
    beam: Optional[str] = "*",
    pol: Optional[str] = "??",
    cal: bool = False,
    noise: bool = False,
    rfi: bool = False,
    data: bool = False,
) -> List[str]:
    """Generate a list of patterns according to the specified options.

    Patterns are used to match components in the ZIP archive of the
    Sentinel-1 products.
    """
    beam = "*" if beam is None else beam
    pol = "??" if pol is None else pol

    patterns = [
        "S1*.SAFE/manifest.safe",
    ]

    head = "S1*.SAFE/annotation"
    tail = f"s1?-{beam}-???-{pol}-*.xml"

    patterns.append(f"{head}/{tail}")
    if cal:
        patterns.append(f"{head}/calibration/calibration-{tail}")
    if noise:
        patterns.append(f"{head}/calibration/noise-{tail}")
    if rfi:
        patterns.append(f"{head}/rfi/rfi-{tail}")

    if data:
        patterns.append(f"S1*.SAFE/measurement/s1?-{beam}-???-{pol}-*.tiff")
        patterns.append(f"S1*.SAFE/s1?-{beam}-???-?-{pol}-*.dat")

    return patterns


def _is_product_complete(
    path: pathlib.Path,
    patterns: Optional[List[str]] = None,
    block_size: Optional[int] = BLOCKSIZE,
) -> bool:
    if not path.is_dir():
        return False

    manifest_path = path / "manifest.safe"
    if not manifest_path.is_file():
        return False

    xmldoc = etree.parse(os.fspath(manifest_path))
    for elem in xmldoc.iterfind("./dataObjectSection/dataObject/byteStream"):
        relative_component_path = elem.find("fileLocation").attrib["href"]
        relative_component_path = pathlib.Path(relative_component_path)
        relative_component_path = relative_component_path.relative_to(".")

        patterns = make_patterns() if not patterns else patterns

        component_path = path.name / relative_component_path
        for pattern in patterns:
            if component_path.match(pattern):
                # pattern matches: exit the current loop and continue
                # in the current main iteration
                break
        else:
            # skip the rest and go to the next main iteration
            continue

        component_path = path / relative_component_path
        if not component_path.is_file():
            return False

        size = int(elem.attrib["size"])
        if component_path.stat().st_size != size:
            return False

        checksum_elem = elem.find("checksum")
        checksum_type = checksum_elem.attrib["checksumName"]
        if checksum_type.upper() != "MD5":
            _log.warning("unexpected checksum type: %s", checksum_type)
            return False  # cannot check if the file is complete
        md5 = hashlib.md5()
        with path.joinpath(relative_component_path).open("rb") as fd:
            for data in iter(functools.partial(fd.read, block_size), b""):
                md5.update(data)
        if md5.hexdigest() != checksum_elem.text:
            return False

    return True


def _filter_components(
    zf: zipfile.ZipFile,
    patterns: List[str],
) -> List[zipfile.ZipInfo]:
    components = []
    for info in zf.filelist:
        for pattern in patterns:
            if fnmatch.fnmatch(info.filename, pattern):
                components.append(info)
                break
    return components


def _download(
    zf: zipfile.ZipFile,
    info: zipfile.ZipInfo,
    outfile: PathType,
    block_size: int = BLOCKSIZE,
    noprogress: bool = False,
):
    size = info.file_size
    with tqdm.tqdm(
        total=size, leave=False, unit_scale=True, unit="B", disable=noprogress
    ) as pbar:
        with zf.open(info) as src, open(outfile, "wb") as dst:
            for data in iter(functools.partial(src.read, block_size), b""):
                dst.write(data)
                pbar.update(len(data))


def download_components_from_urls(
    urls,
    *,
    patterns: Optional[List[str]] = None,
    outdir: PathType = ".",
    auth: Optional[Auth] = None,
    block_size: int = BLOCKSIZE,
    noprogress: bool = False,
):
    """Download Sentinel-1 annotation for the specified product urls."""
    outdir = pathlib.Path(outdir)
    if patterns is None:
        patterns = make_patterns()

    with _ClientType(auth=auth, block_size=block_size) as client:
        url_iter = tqdm.tqdm(urls, unit=" products", disable=noprogress)
        for url in url_iter:
            url_iter.set_description(url)
            product_out_path = outdir / pathlib.Path(urlparse(url).path).name
            product_out_path = product_out_path.with_suffix(".SAFE")
            product_name = product_out_path.stem
            if _is_product_complete(product_out_path, patterns, block_size):
                _log.debug("product already on disk: %r", product_name)
                continue
            else:
                _log.debug("download: %r", product_name)

            with client.open_zip_archive(url) as zf:
                _log.debug("%s open", url)
                components = _filter_components(zf, patterns)
                component_iter = tqdm.tqdm(
                    components, unit="files", leave=False, disable=noprogress
                )
                for info in component_iter:
                    filename = pathlib.Path(info.filename)
                    component_iter.set_description(filename.name)
                    targetdir = outdir / filename.parent
                    outfile = targetdir / filename.name
                    _log.debug("targetdir = %r", targetdir)
                    _log.debug("outfile = %r", outfile)
                    targetdir.mkdir(exist_ok=True, parents=True)
                    if outfile.exists():
                        _log.debug("outfile = %r exists", outfile)
                    else:
                        _download(
                            zf,
                            info,
                            outfile,
                            block_size=block_size,
                            noprogress=noprogress,
                        )
                        _log.debug("%r extracted", info.filename)


def download_annotations(
    products: List[str],
    *,
    patterns: Optional[List[str]] = None,
    outdir: PathType = ".",
    auth: Optional[Auth] = None,
    block_size: Optional[int] = BLOCKSIZE,
    noprogress: bool = False,
):
    """Download annotations for the specified Sentinel-1 products."""
    results = query(products)
    if len(results) != len(products):
        warnings.warn(
            f"only {len(results)} of the {len(products)} requested products "
            f"found on the remote server"
        )

    urls = [item.properties["url"] for item in results]

    download_components_from_urls(
        urls,
        patterns=patterns,
        outdir=outdir,
        auth=auth,
        block_size=block_size if block_size is not None else BLOCKSIZE,
        noprogress=noprogress,
    )


def _get_auth(
    user: Optional[str] = None,
    pwd: Optional[str] = None,
    hostname: Url = "urs.earthdata.nasa.gov",
) -> Auth:
    if user is not None and pwd is not None:
        return Auth(user, pwd)
    elif user is None and pwd is None:
        db = netrc.netrc()
        user, _, pwd = db.authenticators(hostname)
        return Auth(user, pwd)
    else:
        raise ValueError(
            "Both username and password must be provided to authenticate."
        )
