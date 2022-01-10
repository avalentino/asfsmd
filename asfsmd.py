#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK

"""ASF Sentinel-1 Metadata Download tool.

Small Python tool (`asfsmd`) that allows to download XML files containing
Sentinel-1 products metadata from the ASF archive.

Sentinel-1 products are stored in the ASF arcive as ZIP files that are
quite large because they comntain both the products annotations and the
binary image data.

The `asfsmd` tool is able to retrieve only the relatively samll annotation
files (in XML format) without downloading the entire ZIP archive.
"""

import sys
import netrc
import fnmatch
import logging
import pathlib
import zipfile
import argparse
import warnings

from urllib.parse import urlparse

import tqdm
import httpio
import requests
import asf_search as asf


__version__ = "1.0.0"
__all__ = ["download_annotations", "main"]


_log = logging.getLogger(__name__)


BLOACKSIZE = 1 * 1024  # 1kb


class HttpIOFile(httpio.SyncHTTPIOFile):
    def open(self, session=None):
        self._assert_not_closed()
        if not self._closing and self._session is None:
            self._session = requests.Session() if session is None else session
            response = self._session.get(self.url, stream=True, **self._kwargs)
            with response:
                response.raise_for_status()
                try:
                    self.length = int(response.headers["Content-Length"])
                except KeyError:
                    raise httpio.HTTPIOError(
                        "Server does not report content length"
                    )
                accept_ranges = response.headers.get("Accept-Ranges", "")
                if accept_ranges.lower() != "bytes":
                    raise httpio.HTTPIOError(
                        "Server does not accept 'Range' headers"
                    )
        return self


def query(products, auth=None):
    """Query the specified Sentinel-1 products."""
    products = [product + "-SLC" for product in products]
    results = asf.product_search(products)
    return results


def download_annotations_core(urls, outdir=".", auth=None,
                              block_size=BLOACKSIZE):
    """Download Sentinel-1 annotationd for the specified product urls."""
    outdir = pathlib.Path(outdir)

    patterns = [
        "S1*.SAFE/manifest.safe",
        "S1*.SAFE/annotation/s1*.xml",
    ]

    with requests.Session() as session:
        session.auth = auth
        _log.debug("session open")

        url_iter = tqdm.tqdm(urls, unit=" products")
        for url in url_iter:
            url_iter.set_description(url)
            product_name = pathlib.Path(urlparse(url).path).stem
            _log.debug(f"{product_name = }")

            # if outdir.joinpath(product_name).with_suffix('.SAFE').exists():
            #     _log.debug(f'{product_name} already exists')
            #    continue

            _log.debug(f"download: {product_name}")

            remote_file = HttpIOFile(url, block_size=block_size)
            with remote_file.open(session=session) as fd:
                _log.debug(f"{url} open")
                with zipfile.ZipFile(fd) as zf:
                    components = []
                    for info in zf.filelist:
                        for pattern in patterns:
                            if fnmatch.fnmatch(info.filename, pattern):
                                components.append(info)
                                break

                    component_iter = tqdm.tqdm(
                        components, unit="files", leave=False
                    )
                    for info in component_iter:
                        filename = pathlib.Path(info.filename)
                        component_iter.set_description(filename.name)
                        targetdir = outdir / filename.parent
                        outfile = targetdir / filename.name
                        _log.debug(f"{targetdir = }")
                        _log.debug(f"{outfile = }")
                        targetdir.mkdir(exist_ok=True, parents=True)
                        if outfile.exists():
                            _log.debug(f"{outfile = } exists")
                            continue
                        # zf.extract(info, str(targetdir))
                        data = zf.read(info)
                        outfile.write_bytes(data)
                        _log.debug(f"{info.filename} extracted")


def download_annotations(products, outdir=".", auth=None):
    """Download annotationd for the specified Sentinel-1 products."""
    results = query(products, auth=auth)
    if len(results) != len(products):
        warnings.warn(
            f"only {len(results)} of the {len(products)} requested products "
            f"found on the remote server"
        )

    urls = [item.properties["url"] for item in results]

    download_annotations_core(urls, outdir=outdir, auth=auth)


def _get_auth(*, user=None, pwd=None, hostname="urs.earthdata.nasa.gov"):
    if user is not None and pwd is not None:
        return user, pwd
    elif user is None and pwd is None:
        db = netrc.netrc()
        user, _, pwd = db.authenticators(hostname)
        return user, pwd
    else:
        raise ValueError(
            "Both username and password must be provided to authenticate."
        )


# === Command Line Interface ==================================================


try:
    from os import EX_OK
except ImportError:
    EX_OK = 0
EX_FAILURE = 1
EX_INTERRUPT = 130

LOGFMT = "%(asctime)s %(levelname)-8s -- %(message)s"


def _autocomplete(parser):
    try:
        import argcomplete
    except ImportError:
        pass
    else:
        argcomplete.autocomplete(parser)


def _set_logging_control_args(parser, default_loglevel="WARNING"):
    """Set up command line options for logging control."""
    loglevels = [logging.getLevelName(level) for level in range(10, 60, 10)]

    parser.add_argument(
        "--loglevel",
        default=default_loglevel,
        choices=loglevels,
        help="logging level (default: %(default)s)",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        dest="loglevel",
        action="store_const",
        const="ERROR",
        help="suppress standard output messages, "
        "only errors are printed to screen",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="loglevel",
        action="store_const",
        const="INFO",
        help="print verbose output messages",
    )
    parser.add_argument(
        "-d",
        "--debug",
        dest="loglevel",
        action="store_const",
        const="DEBUG",
        help="print debug messages",
    )

    return parser


def _get_parser(subparsers=None):
    """Instantiate the command line argument (sub-)parser."""
    name = pathlib.Path(__file__).stem
    synopsis = __doc__.splitlines()[0]
    doc = __doc__

    if subparsers is None:
        parser = argparse.ArgumentParser(prog=name, description=doc)
        parser.add_argument(
            "--version", action="version", version="%(prog)s v" + __version__
        )
    else:
        parser = subparsers.add_parser(name, description=doc, help=synopsis)
        # parser.set_defaults(func=info)

    parser = _set_logging_control_args(parser)

    # Command line options
    parser.add_argument(
        "-f",
        "--file-list",
        action="store_true",
        help="read the list of products form file. "
        "The file is expected to contain one product name per line.",
    )
    parser.add_argument(
        "-o",
        "--outdir",
        default=".",
        help="path of the output directory (default='%(default)s')",
    )

    parser.add_argument(
        "-u",
        "--username",
        help="username for ASF authentication. "
        "If not provided the tool attempts to retireve the "
        "authentication parameters for the user's '.netrc' file looking "
        "for the host 'urs.earthdata.nasa.gov'",
    )
    parser.add_argument(
        "-p",
        "--password",
        help="password for ASF authentication. "
        "If not provided the tool attempts to retireve the "
        "authentication parameters for the user's '.netrc' file looking "
        "for the host 'urs.earthdata.nasa.gov'",
    )
    parser.add_argument(
        "--block-size",
        type=int,
        default=BLOACKSIZE,
        help="httpio block size in bytes (default: %(default)d)",
    )

    # Positional arguments
    parser.add_argument(
        "inputs",
        nargs="+",
        metavar="INPUT",
        help="Sentinel-1 product name(s). "
        "If the '-f' flag is set then the argument is interpreted as "
        "the filename containing the list of products.",
    )

    if subparsers is None:
        _autocomplete(parser)

    return parser


def _parse_args(args=None, namespace=None, parser=None):
    """Parse command line arguments."""
    if parser is None:
        parser = _get_parser()

    args = parser.parse_args(args, namespace)

    # Common pre-processing of parsed arguments and consistency checks
    # ...

    return args


def main(*argv):
    """Implement the main CLI interface."""
    # setup logging
    logging.basicConfig(format=LOGFMT, level=logging.INFO)  # stream=sys.stdout
    logging.captureWarnings(True)

    # parse cmd line arguments
    args = _parse_args(argv if argv else None)

    # execute main tasks
    exit_code = EX_OK
    try:
        _log.setLevel(args.loglevel)

        products = []
        if args.file_list:
            for filename in args.inputs:
                filename = pathlib.Path(filename)
                products.extend(
                    line for line in filename.read_text().splitlines() if line
                )
        else:
            products.extend(args.inputs)

        auth = _get_auth(user=args.username, pwd=args.password)

        download_annotations(products, outdir=args.outdir, auth=auth)
    except Exception as exc:
        _log.critical(
            "unexpected exception caught: {!r} {}".format(
                type(exc).__name__, exc
            )
        )
        _log.debug("stacktrace:", exc_info=True)
        exit_code = EX_FAILURE
    except KeyboardInterrupt:
        _log.warning("Keyboard interrupt received: exit the program")
        exit_code = EX_INTERRUPT

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
