"""Asfsmd client based on httpio and requests."""

import io
import zipfile
import contextlib

import httpio
import requests

from .common import AbstractClient, Auth, BLOCKSIZE, Url


class HttpIOFile(httpio.SyncHTTPIOFile):
    def open(self, session=None):
        self._assert_not_closed()
        if not self._closing and self._session is None:
            self._session = requests.Session() if session is None else session
            response = self._session.get(self.url, stream=True, **self._kwargs)
            with response:
                response.raise_for_status()
                try:
                    self.length = int(response.headers["Content-Length"])
                except KeyError:
                    raise httpio.HTTPIOError(
                        "Server does not report content length"
                    )
                accept_ranges = response.headers.get("Accept-Ranges", "")
                if accept_ranges.lower() != "bytes":
                    raise httpio.HTTPIOError(
                        "Server does not accept 'Range' headers"
                    )
        return self


class HttpIOClient(AbstractClient):
    def __init__(self, auth: Auth, block_size: int = BLOCKSIZE):
        self._session = requests.Session()
        self._session.auth = auth
        self._block_size = block_size

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._session.close()

    def open(self, url: Url, mode: str = "rb") -> io.BufferedIOBase:
        if mode != "rb":
            raise ValueError("invalid mode: {mode!r}")

        remote_file = HttpIOFile(url, block_size=self._block_size)
        return remote_file.open(session=self._session)

    @contextlib.contextmanager
    def open_zip_archive(self, url: Url) -> zipfile.ZipFile:
        with self.open(url) as fd:
            with zipfile.ZipFile(fd) as zf:
                yield zf


Client = HttpIOClient
