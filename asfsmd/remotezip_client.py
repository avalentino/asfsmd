"""Asfsmd client based on remotezip."""

import zipfile

import requests
import remotezip

from .common import AbstractClient, Auth, BLOCKSIZE, Url


class RemoteZipCLient(AbstractClient):
    """RemoteZip based asfsmd client."""

    def __init__(self, auth: Auth, block_size: int = BLOCKSIZE):
        """Initialize the remotezip based client."""
        self._session = requests.Session()
        self._session.auth = auth
        self._block_size = block_size

    def __exit__(self, exc_type, exc_value, traceback):  # noqa: D105
        self._session.close()

    def open_zip_archive(self, url: Url) -> zipfile.ZipFile:
        """Context manager for the remote zip archive."""
        return remotezip.RemoteZip(
            url, session=self._session, initial_buffer_size=self._block_size
        )


Client = RemoteZipCLient
