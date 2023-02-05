"""Common constants and types."""

import os
import abc
from typing import NamedTuple, Union

MB = 1024 * 1024
BLOCKSIZE = 16 * MB  # 16MB (64MB is a better choice to download data)


PathType = Union[str, bytes, os.PathLike]
Url = str


class Auth(NamedTuple):
    """Authentication parameters."""

    user: str
    pwd: str


class AbstractClient(abc.ABC):
    """Base asfsmd client class."""

    def __enter__(self):  # noqa: D105
        return self

    def __exit__(self, exc_type, exc_value, traceback):  # noqa: D105
        pass

    @abc.abstractmethod
    def open_zip_archive(self, url: Url):
        """Context manager for the remote zip archive."""
        pass
