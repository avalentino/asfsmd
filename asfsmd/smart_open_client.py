"""Asfsmd client based on smart-open."""

import zipfile
import contextlib
from typing import Optional

import smart_open

from .common import AbstractClient, Auth, Url


class SmartOpenClient(AbstractClient):
    """SmartOpen based asfsmd client."""

    def __init__(self, auth: Auth, block_size: Optional[int] = None):
        """Initialize the smartopen based client."""
        self.client_kwargs = None
        if auth is not None:
            self.client_kwargs["user"] = auth.user
            self.client_kwargs["password"] = auth.pwd
        if block_size is not None:
            self.client_kwargs["buffer_size"] = block_size

    @contextlib.contextmanager
    def open_zip_archive(self, url: Url) -> zipfile.ZipFile:
        """Context manager for the remote zip archive."""
        with smart_open.open(url, "rb", **self.client_kwargs) as fd:
            with zipfile.ZipFile(fd) as zf:
                yield zf


Client = SmartOpenClient
