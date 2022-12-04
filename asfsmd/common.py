"""Common constants and types."""

import os
import abc
from typing import NamedTuple, Union


MB = 1024 * 1024
BLOCKSIZE = 16 * MB  # 16MB (64MB is a better choice to download data)


PathType = Union[str, bytes, os.PathLike]
Url = str


class Auth(NamedTuple):
    user: str
    pwd: str


class AbstractClient(abc.ABC):
    @abc.abstractmethod
    def open_zip_archive(self, url: Url):
        pass
