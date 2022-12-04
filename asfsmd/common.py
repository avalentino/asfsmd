"""Common constants and types."""

import os
from typing import NamedTuple, Union


MB = 1024 * 1024
BLOCKSIZE = 16 * MB  # 16MB (64MB is a better choice to download data)


PathType = Union[str, bytes, os.PathLike]
Url = str


class Auth(NamedTuple):
    user: str
    pwd: str
