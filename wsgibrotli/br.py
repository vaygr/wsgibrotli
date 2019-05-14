# -*- coding: utf-8 -*-

import re
import sys

import brotli


__all__ = ['BrotliMiddleware']

# Python 2 compatibility
PY2 = sys.version_info[0] == 2

_RE_BROTLI = re.compile(r'\bbr\b')

_DEFAULT_QUALITY = 4


class _BrotliIterWrapper(object):

    def __init__(self, app_iter, brotli_middleware):
        self._b = brotli_middleware

        self._next = getattr(iter(app_iter), 'next' if PY2 else '__next__')
        self._last = False
        self._finished = False

        if hasattr(app_iter, 'close'):
            self.close = app_iter.close

    def __iter__(self):
        return self

    def next(self):
        if not self._last:
            try:
                data = self._next()
            except StopIteration:
                self._last = True

        if not self._last:
            if self._b.brotli_ok:
                return self._b.brotli_data(data)
            else:
                return data
        else:
            if not self._finished:
                self._finished = True

                return self._b.brotli_trailer()

            raise StopIteration

        return self._b.brotli_data(data) if self._b.brotli_ok else data

    def __next__(self):
        return self.next()


class _BrotliMiddleware(object):

    def __init__(self, start_response, mime_types, quality, etag_alter):
        self._start_response = start_response
        self._mime_types = mime_types
        self._etag_alter = etag_alter
        self._compress = brotli.Compressor(quality=quality)

        self.brotli_ok = False

    def brotli_data(self, data):
        return self._compress.process(data)

    def brotli_trailer(self):
        return self._compress.flush() + self._compress.finish()

    def start_response(self, status, headers, exc_info=None):
        self.brotli_ok = False

        for name, value in headers:
            name = name.lower()

            if name == 'content-type':
                for p in self._mime_types:
                    if p.match(value) is not None:
                        self.brotli_ok = True

                        break
            elif name == 'content-encoding':
                self.brotli_ok = False

                break

        if self.brotli_ok:
            _headers = []

            for name, value in headers:
                # Strip Content-Length for compressed data
                if name.lower() == 'content-length':
                    continue

                if name.lower() == 'etag' and self._etag_alter:
                    _headers.append((name, re.sub(r'"$', r';br"', value)))

                    continue

                _headers.append((name, value))

            _headers.append(('Content-Encoding', 'br'))
        else:
            _headers = headers

        _write = self._start_response(status, _headers, exc_info)

        if self.brotli_ok:
            def write_brotli(data):
                _write(self.brotli_data(data))

            return write_brotli
        else:
            return _write


class BrotliMiddleware(object):

    def __init__(self, application, mime_types=None, quality=_DEFAULT_QUALITY, etag_alter=False):
        if mime_types is None:
            mime_types = ['text/.*']

        self._application = application
        self._mime_types = [re.compile(m) for m in mime_types]
        self._quality = quality
        self._etag_alter = etag_alter

    def __call__(self, environ, start_response):
        if not _RE_BROTLI.search(environ.get('HTTP_ACCEPT_ENCODING', '')):
            return self._application(environ, start_response)

        b = _BrotliMiddleware(start_response, self._mime_types, self._quality, self._etag_alter)

        result = self._application(environ, b.start_response)

        try:
            shortcut = len(result) == 1
        except TypeError:
            shortcut = False

        if shortcut:
            try:
                i = iter(result)
                data = next(i)

                if b.brotli_ok:
                    return [b.brotli_data(data) + b.brotli_trailer()]
                else:
                    return [data]
            finally:
                if hasattr(result, 'close'):
                    result.close()

        return _BrotliIterWrapper(result, b)
