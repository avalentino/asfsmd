asfsmd release history
======================


asfsmd v1.4.0 (05/02/2023)
--------------------------

* Support for non SLC products (including RAW).
* Move setup configuration to `pyproject.toml`.
* Improved formatting to be compatible with the `black` tool.


asfsmd v1.3.0 (18/12/2022)
--------------------------

* New client based on smart_open_.

.. _smart_open: https://github.com/RaRe-Technologies/smart_open


asfsmd v1.2.0 (04/12/2022)
--------------------------

* Refactoring to convert the `asfsmd.py` module into a package.
* Support multiple backends for remote file access: httpio_, fsspec_ and
  remotezip_.
  The httpio based implementation seems to be slightly faster w.r.t. the
  other ones.
* Fix issue with the management of default values for the `make_patterns`
  function.
* Improve the management of the download of large files (chunking and
  progress).

.. _httpio: https://github.com/barneygale/httpio
.. _fsspec: https://github.com/fsspec/filesystem_spec
.. _remotezip: https://github.com/gtsystem/python-remotezip


asfsmd v1.1.0 (03/12/2022)
--------------------------

* Now it is possible to customize the selection of files to be downloaded.
  Beyond the manifest and the annotation files, now it is also possible to
  download:

  * calibration annotations
  * noise annotations
  * rfi annotations
  * measurement files

  Moreover now it is possible to select a specific beams or polarizations.
  Patch developed by @scottstanie and @avalentino.
* Restore compatibility with Python 3.6.


asfsmd v1.0.0 (09/01/2022)
--------------------------

Initial release.
