ASF Sentinel-1 Metadata Download tool
=====================================

:copyright: 2021-2022 Antonio Valentino

Small Python tool (`asfsmd`) that allows to download XML files containing
Sentinel-1 products metadata from the ASF archive.

Sentinel-1 products are stored in the ASF arcive as ZIP files that are
quite large because they comntain both the products annotations and the
binary image data.

The `asfsmd` tool is able to retrieve only the relatively samll annotation
files (in XML format) without downloading the entire ZIP archive.

`asfsmd` exploits the `httpio` Python package for reading HTTP resources
as random-access file-like objects. In order to do it the remote server
must support the `Range` header.

This approach allows to open the ZIP archive remotely, inspects contents, and
download only the pieces of data that are actually necessary to the user.

Performnces of this approach are quite poor but, in the specific case of
Sentinel-1 products, the entire process results to be faster than downloading
the entire ZIP archive and extracting only annotation files.


Command Line Interface
----------------------

::

    $ python3 asfsmd.py --help

    usage: asfsmd [-h] [--version]
                  [--loglevel {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                  [-q] [-v] [-d] [-f] [-o OUTDIR] [-u USERNAME] [-p PASSWORD]
                  INPUT [INPUT ...]

    ASF Sentinel-1 Metadata Download tool. Small Python tool (`asfsmd`) that
    allows to download XML files containing Sentinel-1 products metadata from
    the ASF archive. Sentinel-1 products are stored in the ASF arcive as ZIP
    files that are quite large because they comntain both the products
    annotations and the binary image data. The `asfsmd` tool is able to
    retrieve only the relatively samll annotation files (in XML format) without
    downloading the entire ZIP archive.

    positional arguments:
      INPUT                 Sentinel-1 product name(s). If the '-f' flag is set
                            then the argument is interpreted as the filename
                            containing the list of products.

    options:
      -h, --help            show this help message and exit
      --version             show program's version number and exit
      --loglevel {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                            logging level (default: WARNING)
      -q, --quiet           suppress standard output messages, only errors are
                            printed to screen
      -v, --verbose         print verbose output messages
      -d, --debug           print debug messages
      -f, --file-list       read the list of products form file. The file is
                            expected to contain one product name per line.
      -o OUTDIR, --outdir OUTDIR
                            path of the output directory (default='.')
      -u USERNAME, --username USERNAME
                            username for ASF authentication. If not provided
                            the tool attempts to retireve the authentication
                            parameters for the user's '.netrc' file looking
                            for the host 'urs.earthdata.nasa.gov'
      -p PASSWORD, --password PASSWORD
                            password for ASF authentication. If not provided
                            the tool attempts to retireve the authentication
                            parameters for the user's '.netrc' file looking
                            for the host 'urs.earthdata.nasa.gov'
      --block-size BLOCK_SIZE
                            httpio block size in bytes (default: 8192)


License
-------

The `asfsmd` package is distributed under the MIT License.
