# -*- coding: utf-8 -*-

from wsgibrotli.br import BrotliMiddleware, _DEFAULT_QUALITY


_TEXT_TYPES = ['text/xml', 'application/xml', 'application/xhtml+xml',
               'text/html', 'text/plain']


def br(mime_types=None, quality=_DEFAULT_QUALITY, etag_alter=False):
    '''
    @param mime_types Mimetypes that middleware should compress (default: None)
    @param quality Brotli compression level 0-11, 11 is max (default: 4)
    @param etag_alter Add compression method to ETag HTTP header (default: False)
    '''
    if mime_types is None:
        mime_types = _TEXT_TYPES

    def decorator(application):
        return BrotliMiddleware(application, mime_types, quality, etag_alter)

    return decorator
