#!/usr/bin/env python3

import fnmatch
import logging
import pathlib
import zipfile
import itertools
from urllib.parse import urlparse

import tqdm
import httpio
import requests
import asf_search as asf


PRODUCTS = [
    'S1A_IW_SLC__1SDV_20210502T171502_20210502T171529_037712_04733D_777C',
    'S1A_IW_SLC__1SDV_20210502T171527_20210502T171554_037712_04733D_DE21',
    'S1A_IW_SLC__1SDV_20210514T171503_20210514T171530_037887_0478B1_3294',
    'S1A_IW_SLC__1SDV_20210514T171528_20210514T171555_037887_0478B1_2954',
    'S1A_IW_SLC__1SDV_20210506T053504_20210506T053531_037763_0474F3_0892',
    'S1A_IW_SLC__1SDV_20210506T053529_20210506T053556_037763_0474F3_EA2A',
    'S1B_IW_SLC__1SDV_20210512T053432_20210512T053459_026867_0335B6_81DE',
    'S1B_IW_SLC__1SDV_20210512T053457_20210512T053524_026867_0335B6_160F',
]
# PRODUCTS = list(itertools.chain(*PRODUCTS.values()))
# print(PRODUCTS.values())

_log = logging.getLogger(__name__)


class HttpIOFile(httpio.SyncHTTPIOFile):
    def open(self, session=None):
        self._assert_not_closed()
        if not self._closing and self._session is None:
            self._session = requests.Session() if session is None else session
            response = self._session.get(self.url, stream=True, **self._kwargs)
            with response:
                response.raise_for_status()
                try:
                    self.length = int(response.headers['Content-Length'])
                except KeyError:
                    raise httpio.HTTPIOError(
                        "Server does not report content length")
                if response.headers.get('Accept-Ranges', '').lower() != 'bytes':
                    raise httpio.HTTPIOError(
                        "Server does not accept 'Range' headers")
        return self


def query(products, auth=None):
    products = [product + '-SLC' for product in products]
    results = asf.product_search(products)
    return results


def download_annotations_core(urls, outdir='.', auth=None):
    outdir = pathlib.Path(outdir)

    patterns = [
        'S1*.SAFE/manifest.safe',
        'S1*.SAFE/annotation/s1*.xml'
    ]

    with requests.Session() as session:
        session.auth = auth
        _log.debug('session open')

        url_iter = tqdm.tqdm(urls, unit=' products')
        for url in url_iter:
            url_iter.set_description(url)
            product_name = pathlib.Path(urlparse(url).path).stem
            _log.debug(f'{product_name = }')
            
            # if outdir.joinpath(product_name).with_suffix('.SAFE').exists():
            #     _log.debug(f'{product_name} already exists')
            #    continue

            _log.debug(f'download: {product_name}')

            with HttpIOFile(url).open(session=session) as fd:
                _log.debug(f'{url} open')
                with zipfile.ZipFile(fd) as zf:
                    component_iter = tqdm.tqdm(zf.filelist, unit='files')
                    for info in component_iter:
                        component_iter.set_description(info.filename)
                        for pattern in patterns:
                            if fnmatch.fnmatch(info.filename, pattern):
                                break
                        else:
                            continue
                        targetdir = outdir / pathlib.Path(info.filename).parent
                        outfile = targetdir / pathlib.Path(info.filename).name
                        _log.debug(f'{targetdir = }')
                        _log.debug(f'{outfile = }')
                        targetdir.mkdir(exist_ok=True, parents=True)
                        if outfile.exists():
                            _log.debug(f'{outfile = } exists')
                            continue
                        # zf.extract(info, str(targetdir))
                        data = zf.read(info)
                        outfile.write_bytes(data)
                        _log.debug(f'{info.filename} extracted')


def download_annotations(products, outdir='.', auth=None):
    results = query(products, auth=auth)
    assert len(results) == len(products)

    urls = [item.properties['url'] for item in results]

    download_annotations_core(urls, outdir=outdir, auth=auth)


def _get_auth():
    import netrc
    db = netrc.netrc()
    user, _, pwd = db.authenticators('urs.earthdata.nasa.gov')
    return user, pwd


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s'
    )
    logging.getLogger(__name__).setLevel(logging.DEBUG)

    download_annotations(PRODUCTS, outdir='asf-out', auth=_get_auth())
