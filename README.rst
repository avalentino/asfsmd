ASF Sentinel-1 Metadata Download tool
=====================================

Small Python tool (`asfsmd`) that allows to download XML files containing
Sentinel-1 products metadata from the ASF archive.

Sentinel-1 products are stored in the ASF arcive as ZIP files that are
quite large because they contain both the products annotations and the
binary image data.

The `asfsmd` tool is able to retrieve only the relatively samll annotation
files (in XML format) without downloading the entire ZIP archive.

`asfsmd` exploits Python packages like `fsspec` or `httpio` for reading HTTP
resources as random-access file-like objects. In order to do it the remote
server must support the `Range` header.

This approach allows to open the ZIP archive remotely, inspects contents, and
download only the pieces of data that are actually necessary to the user.

Performnces of this approach are quite poor but, in the specific case of
Sentinel-1 products, the entire process results to be faster than downloading
the entire ZIP archive and extracting only annotation files.


Command Line Interface
----------------------

::

    $ python3 -m asfsmd --help

    usage: asfsmd [-h] [--version]
                  [--loglevel {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                  [-q] [-v] [-d]
                  [-f] [--urls] [-o OUTDIR] [-u USERNAME] [-p PASSWORD]
                  [--block-size BLOCK_SIZE]
                  [-b {s1,s2,s3,s4,s5,s6,iw1,iw2,iw3,ew1,ew2,ew3,ew4,ew5,wv1,wv2}]
                  [--pol {vv,vh,hv,hh}] [-c] [-n] [-r] [--data]
                  INPUT [INPUT ...]

    ASF Sentinel-1 Metadata Download tool. Small Python tool (`asfsmd`) that
    allows to download XML files containing Sentinel-1 products metadata from
    the ASF archive. Sentinel-1 products are stored in the ASF arcive as ZIP
    files that are quite large because they comntain both the products
    annotations and the binary image data. The `asfsmd` tool is able to
    retrieve only the relatively small annotation files (in XML format) without
    downloading the entire ZIP archive.

    positional arguments:
      INPUT                 Sentinel-1 product name(s). If the '-f' flag is set
                            then the argument is interpreted as the filename
                            containing the list of products. If the '--urls'
                            flag is set then the arguments are interpreted as
                            URLs pointing to product on the ASF server.
                            See '--file--list' and the '--urls' options for
                            more details.

    options:
      -h, --help            show this help message and exit
      --version             show program's version number and exit
      --loglevel {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                            logging level (default: WARNING)
      -q, --quiet           suppress standard output messages, only errors are
                            printed to screen
      -v, --verbose         print verbose output messages
      -d, --debug           print debug messages
      -f, --file-list       read the list of products from a file. The file
                            can be a JSON file (with '.json' extension) or a
                            text file.The text file is expected to contain one
                            product name per line.The json file can contain a
                            list of products or a dictionary containing a list
                            of products for each key.In this case the key is
                            used as sub-folder name to store the corresponding
                            products.Example: <OUTDIR>/<KEY>/<PRODUCT>
      --urls                Indicate the inputs are a list of URLs from ASF.
      -o OUTDIR, --outdir OUTDIR
                            path of the output directory (default='.')
      -u USERNAME, --username USERNAME
                            username for ASF authentication. If not provided
                            the tool attempts to retrieve the authentication
                            parameters for the user's '.netrc' file looking
                            for the host 'urs.earthdata.nasa.gov'
      -p PASSWORD, --password PASSWORD
                            password for ASF authentication. If not provided
                            the tool attempts to retrieve the authentication
                            parameters for the user's '.netrc' file looking
                            for the host 'urs.earthdata.nasa.gov'
      --block-size BLOCK_SIZE
                            httpio block size in bytes (default: 1024)
      -b {s1,s2,s3,s4,s5,s6,iw1,iw2,iw3,ew1,ew2,ew3,ew4,ew5,wv1,wv2},
      --beam {s1,s2,s3,s4,s5,s6,iw1,iw2,iw3,ew1,ew2,ew3,ew4,ew5,wv1,wv2}
                            Choose only one beam to download. If not provided
                            all beams are downloaded.
      --pol {vv,vh,hv,hh}   Choose only one polarization to download. If not
                            provided both polarizations are downloaded.
      -c, --cal             Download calibration files.
      -n, --noise           Download noise calibration files.
      -r, --rfi             Download RFI files.
      --data                Download measurement files.


License
-------

Copyright (c) 2021-2022 Antonio Valentino

The `asfsmd` package is distributed under the MIT License.
