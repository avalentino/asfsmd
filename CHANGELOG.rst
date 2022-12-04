asfsmd release history
======================


asfsmd v1.2.0 (UNRELEASED)
--------------------------

* Refactoring to convert the `asfsmd.py`` module into a package.
* Support multiple backends for remote file access: httpio, fsspec, remotezip.
  The httpio based implementation seems to be slightly faster w.r.t. the
  other ones.
* Fix issue with the management of default values for the `make_patterns`
  function.
* Improve the management of the download of large files (chunking and
  progress).


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
