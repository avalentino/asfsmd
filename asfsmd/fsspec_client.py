"""Asfsmd client based on fsspec."""

import zipfile
import contextlib
from typing import Optional

import fsspec
import aiohttp

from .common import AbstractClient, Auth, Url


class FsspacClient(AbstractClient):
    """Fsspec based asfsmd client."""

    def __init__(self, auth: Auth, block_size: Optional[int] = None):
        """Initialize the fsspec based client."""
        client_kwargs = None
        if auth is not None:
            user, pwd = auth
            auth = aiohttp.BasicAuth(user, pwd)
            client_kwargs = {"auth": auth}

        self._fs = fsspec.filesystem(
            "http",
            block_size=block_size,
            client_kwargs=client_kwargs,
        )

    @contextlib.contextmanager
    def open_zip_archive(self, url: Url) -> zipfile.ZipFile:
        """Context manager for the remote zip archive."""
        with self._fs.open(url, "rb") as fd:
            with zipfile.ZipFile(fd) as zf:
                yield zf


Client = FsspacClient
