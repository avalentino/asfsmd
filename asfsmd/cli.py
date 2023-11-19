"""Command Line Interface (CLI) for the ASF S1 Metadata Download tool."""

# PYTHON_ARGCOMPLETE_OK


import logging
import pathlib
import argparse
import collections
from typing import Dict, Iterable, List, Optional

import tqdm

from . import __version__
from . import __doc__ as _pkg_doc
from .core import (
    download_annotations,
    download_components_from_urls,
    make_patterns,
    _get_auth,
)
from ._utils import unique, load_product_lists
from .common import BLOCKSIZE, MB

try:
    from os import EX_OK
except ImportError:
    EX_OK = 0
EX_FAILURE = 1
EX_INTERRUPT = 130

LOGFMT = "%(asctime)s %(levelname)-8s -- %(message)s"


def asfsmd_cli(
    inputs: Iterable[str],
    beam: Optional[str] = "*",
    pol: Optional[str] = "??",
    cal: bool = False,
    noise: bool = False,
    rfi: bool = False,
    data: bool = False,
    outdir: str = ".",
    urls: bool = False,
    file_list: bool = False,
    block_size: int = BLOCKSIZE,
    noprogress: bool = False,
    username: Optional[str] = None,
    password: Optional[str] = None,
):
    """High level function for ASF S1 Metadata Download."""
    auth = _get_auth(user=username, pwd=password)
    outroot = pathlib.Path(outdir)
    patterns = make_patterns(
        beam=beam,
        pol=pol,
        cal=cal,
        noise=noise,
        rfi=rfi,
        data=data,
    )

    if urls:
        download_components_from_urls(
            inputs,
            patterns=patterns,
            outdir=outroot,
            auth=auth,
            block_size=block_size,
            noprogress=noprogress,
        )
    else:
        products_tree: Dict[str, List[str]] = collections.defaultdict(list)
        if file_list:
            products_tree = load_product_lists(*inputs)
        else:
            # Ignore if user passed files with .zip or .SAFE extensions
            products_tree[""].extend(
                unique(
                    p.replace(".zip", "").replace(".SAFE", "") for p in inputs
                )
            )

        items = pbar = tqdm.tqdm(products_tree.items(), disable=noprogress)
        for folder, products in items:
            pbar.set_description(folder if folder else "DOWNLOAD")
            outpath = outroot / folder
            download_annotations(
                products,
                outdir=outpath,
                auth=auth,
                patterns=patterns,
                block_size=block_size,
                noprogress=noprogress,
            )

    return EX_OK


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
    name = __package__
    synopsis = __doc__.splitlines()[0]
    doc = _pkg_doc

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
        help="read the list of products from a file. "
        "The file can be a JSON file (with '.json' extension) or a text file."
        "The text file is expected to contain one product name per line."
        "The json file can contain a list of products or a dictionary "
        "containing a list of products for each key."
        "In this case the key is used as sub-folder name to store the "
        "corresponding products."
        "Example: <OUTDIR>/<KEY>/<PRODUCT>",
    )
    parser.add_argument(
        "--urls",
        action="store_true",
        help="Indicate the inputs are a list of URLs from ASF.",
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
        "If not provided the tool attempts to retrieve the "
        "authentication parameters for the user's '.netrc' file looking "
        "for the host 'urs.earthdata.nasa.gov'",
    )
    parser.add_argument(
        "-p",
        "--password",
        help="password for ASF authentication. "
        "If not provided the tool attempts to retrieve the "
        "authentication parameters for the user's '.netrc' file looking "
        "for the host 'urs.earthdata.nasa.gov'",
    )
    parser.add_argument(
        "--block-size",
        type=int,
        default=BLOCKSIZE // MB,
        help="httpio block size in MB (default: %(default)d)",
    )

    # Optional filters
    parser.add_argument(
        "-b",
        "--beam",
        choices=[
            "s1",
            "s2",
            "s3",
            "s4",
            "s5",
            "s6",
            "iw1",
            "iw2",
            "iw3",
            "ew1",
            "ew2",
            "ew3",
            "ew4",
            "ew5",
            "wv1",
            "wv2",
        ],
        type=str.lower,
        help="Choose only one beam to download. "
        "If not provided all beams are downloaded.",
    )

    parser.add_argument(
        "--pol",
        choices=["vv", "vh", "hv", "hh"],
        type=str.lower,
        help="Choose only one polarization to download. "
        "If not provided both polarizations are downloaded.",
    )

    # Additional file downloads
    parser.add_argument(
        "-c", "--cal", action="store_true", help="Download calibration files."
    )
    parser.add_argument(
        "-n",
        "--noise",
        action="store_true",
        help="Download noise calibration files.",
    )
    parser.add_argument(
        "-r", "--rfi", action="store_true", help="Download RFI files."
    )
    parser.add_argument(
        "--data", action="store_true", help="Download measurement files."
    )
    parser.add_argument(
        "--noprogress", action="store_true", help="Disable teh progress bar."
    )

    # Positional arguments
    parser.add_argument(
        "inputs",
        nargs="+",
        metavar="INPUT",
        help="Sentinel-1 product name(s). "
        "If the '-f' flag is set then the argument is interpreted as "
        "the filename containing the list of products. "
        "If the '--urls' flag is set then the arguments are interpreted as "
        "URLs pointing to product on the ASF server. "
        "See '--file-list' and the '--urls' options for more details.",
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
    _log = logging.getLogger(__name__)

    # parse cmd line arguments
    args = _parse_args(argv if argv else None)

    # execute main tasks
    exit_code = EX_OK
    try:
        logging.getLogger().setLevel(args.loglevel)

        exit_code = asfsmd_cli(
            inputs=args.inputs,
            beam=args.beam,
            pol=args.pol,
            cal=args.cal,
            noise=args.noise,
            rfi=args.rfi,
            data=args.data,
            outdir=args.outdir,
            urls=args.urls,
            file_list=args.file_list,
            block_size=args.block_size * MB,
            noprogress=args.noprogress,
            username=args.username,
            password=args.password,
        )
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
