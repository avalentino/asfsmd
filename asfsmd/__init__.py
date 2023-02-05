"""ASF Sentinel-1 Metadata Download tool.

Small Python tool (`asfsmd`) that allows to download XML files containing
Sentinel-1 products metadata from the ASF archive.

Sentinel-1 products are stored in the ASF arcive as ZIP files that are
quite large because they comntain both the products annotations and the
binary image data.

The `asfsmd` tool is able to retrieve only the relatively small annotation
files (in XML format) without downloading the entire ZIP archive.
"""

from .core import (  # noqa: F401
    download_annotations,
    download_components_from_urls,
    make_patterns,
)

__version__ = "1.4.0"
