"""Core functiond for the ASF Sentinel-1 Metadata Download tool."""

import os
import netrc
import fnmatch
import logging
import pathlib
import zipfile
import warnings
import functools
import importlib
from typing import List, Optional
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
    beam="*",
    pol="??",
    cal=False,
    noise=False,
    rfi=False,
    data=False,
):
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
):
    size = info.file_size
    with tqdm.tqdm(total=size, leave=False, unit_scale=True, unit="B") as pbar:
        with zf.open(info) as src, open(outfile, "wb") as dst:
            for data in iter(functools.partial(src.read, block_size), b""):
                dst.write(data)
                pbar.update(len(data))


def download_components_from_urls(
    urls,
    *,
    patterns: Optional[List[str]] = None,
    outdir: PathType = ".",
    auth: Auth = None,
    block_size: Optional[int] = BLOCKSIZE,
):
    """Download Sentinel-1 annotation for the specified product urls."""
    outdir = pathlib.Path(outdir)
    if patterns is None:
        patterns = make_patterns()

    with _ClientType(auth=auth, block_size=block_size) as client:
        url_iter = tqdm.tqdm(urls, unit=" products")
        for url in url_iter:
            url_iter.set_description(url)
            product_name = pathlib.Path(urlparse(url).path).stem
            _log.debug("download: %r", product_name)

            with client.open_zip_archive(url) as zf:
                _log.debug("%s open", url)
                components = _filter_components(zf, patterns)
                component_iter = tqdm.tqdm(
                    components, unit="files", leave=False
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
                        _download(zf, info, outfile, block_size=block_size)
                        _log.debug("%r extracted", info.filename)


def download_annotations(
    products: List[str],
    *,
    patterns: Optional[List[str]] = None,
    outdir: PathType = ".",
    auth: Auth = None,
    block_size: Optional[int] = BLOCKSIZE,
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
        block_size=block_size,
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
