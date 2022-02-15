"Wrapper for WSGI application"

import time
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
        self._reader = reader or uwsgi.chunked_read_nb

    def _read(self):
        "Read whatever is available."
        # NOTE: We always return bytes.
        if self._eof:
            return b''

        while True:
            chunk = self._reader()
            if chunk == b'':
                LOGGER.debug('_read(): EOF')
                self._eof = True
                return b''
            elif chunk is None:
                LOGGER.debug('_read(): None, try again.')
                # No data available.
                time.sleep(0.01)
                continue
            else:
                LOGGER.debug('_read(): %i bytes', len(chunk))
                return chunk

    def read(self, size=None):
        "Read chunked input"
        while True:
            # Read until we satisfy request or we run out of data. Buffer
            # anything left over.
            chunk, self._buffer = self._buffer + self._read(), b''
            if size is None and not self._eof:
                self._buffer = chunk
                continue
            if size and size < len(chunk):
                self._buffer = chunk[size:]
                chunk = chunk[:size]
            elif size and size > len(chunk) and not self._eof:
                self._buffer = chunk
                continue
            return chunk


class Chunked:
    "WSGI application wrapper."

    def __init__(self, app, stream=False):
        LOGGER.debug('__init__(): self=%s, stream=%s', self, stream)
        self.app = app
        self.stream = stream

    def __call__(self, environ, start_response):
        if environ.get('HTTP_TRANSFER_ENCODING', '').lower() == 'chunked':
            if uwsgi is None:
                raise RuntimeError('Not running under uwsgi, cannot support '
                                   'chunked encoding')
            LOGGER.debug('Handling chunked request: self=%s, stream=%s', self, self.stream)
            chunked = _ChunkedStream()

            if not self.stream:
                wsgi_input = BytesIO(chunked.read())
                length = wsgi_input.getbuffer().nbytes
                LOGGER.debug(
                    'Setting wsgi.input and Content-Length: %i', length)
                environ['wsgi.input'] = wsgi_input
                environ['CONTENT_LENGTH'] = length
                wsgi_input.seek(0)

            else:
                environ['wsgi.input'] = chunked

        return self.app(environ, start_response)
