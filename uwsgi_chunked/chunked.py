"Wrapper for WSGI application"

import logging
from io import BytesIO

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())

READ_SIZE = 8192

try:
    import uwsgi

except ImportError:
    uwsgi = None
    LOGGER.warning('Not running under uwsgi')


class _ChunkedStream:
    "Chunked input stream."
    def __init__(self, reader=None):
        self._buffer = b''
        self._eof = False
        self._reader = reader or uwsgi.chunked_read

    def _read(self):
        "Read whatever is available."
        # NOTE: We always return bytes.
        if self._eof:
            return b''

        try:
            chunk = self._reader()
            if chunk == b'':
                self._eof = True
            return chunk

        # pylint: disable=W0703
        except Exception:
            return b''

    def read(self, size=None):
        "Read chunked input"
        while True:
            # Read until we satisfy request or we run out of data. Buffer
            # anything left over.
            chunk, self._buffer = self._buffer + self._read(), b''
            if not size or size == len(chunk):
                chunk = chunk or None
            elif size < len(chunk):
                self._buffer = chunk[size:]
                chunk = chunk[:size]
            elif size > len(chunk) and not self._eof:
                self._buffer = chunk
                continue
            return chunk


def _read_all(environ, chunked):
    "Read entire request and populate wsgi.input and Content-Length header."
    wsgi_input = BytesIO()
    while True:
        chunk = chunked.read(READ_SIZE)
        LOGGER.debug('Read chunk: %s', chunk)
        if chunk == b'':
            break
        wsgi_input.write(chunk)
    environ['CONTENT_LENGTH'] = str(wsgi_input.tell())
    environ['wsgi.input'] = wsgi_input
    wsgi_input.seek(0)


class Chunked:
    "WSGI application wrapper."

    def __init__(self, app, stream=False):
        self.app = app
        self.stream = stream

    def __call__(self, environ, start_response):
        if environ.get('HTTP_TRANSFER_ENCODING', '').lower() == 'chunked':
            if uwsgi is None:
                raise RuntimeError('Not running under uwsgi, cannot support '
                                   'chunked encoding')
            chunked = _ChunkedStream()
            if not self.stream:
                _read_all(environ, chunked)

            else:
                environ['wsgi.input'] = chunked

        return self.app(environ, start_response)
