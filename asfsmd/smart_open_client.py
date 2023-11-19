"""Asfsmd client based on smart-open."""

import zipfile
import contextlib
from typing import Any, Dict, Iterator, Optional

import smart_open

from .common import AbstractClient, Auth, Url


class SmartOpenClient(AbstractClient):
    """SmartOpen based asfsmd client."""

    def __init__(self, auth: Auth, block_size: Optional[int] = None):
        """Initialize the smartopen based client."""
        client_kwargs: Dict[str, Any] = {}
        if auth is not None:
            client_kwargs["user"] = auth.user
            client_kwargs["password"] = auth.pwd
        if block_size is not None:
            client_kwargs["buffer_size"] = block_size
        self.client_kwargs = client_kwargs if client_kwargs else None

    @contextlib.contextmanager
    def open_zip_archive(self, url: Url) -> Iterator[zipfile.ZipFile]:
        """Context manager for the remote zip archive."""
        with smart_open.open(url, "rb", **self.client_kwargs) as fd:
            with zipfile.ZipFile(fd) as zf:
                yield zf


Client = SmartOpenClient
