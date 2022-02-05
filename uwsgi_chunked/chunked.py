import logging
from io import BytesIO

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())

try:
    import uwsgi

except ImportError:
    uwsgi = None
    LOGGER.warn('Not running under uwsgi')


def _read_chunked(environ):
    input = BytesIO()
    while True:
        chunk = uwsgi.chunked_read()
        if chunk == b'':
            break
        input.write(chunk)
    environ['CONTENT_LENGTH'] = str(input.tell())
    environ['wsgi.input'] = input
    input.seek(0)


class _ChunkedStream:
    def read(self, size=None):
        return uwsgi.chunked_read()


class Chunked:
    def __init__(self, app, stream=False):
        self.app = app
        self.stream = stream

    def __call__(self, environ, start_response):
        if environ.get('HTTP_TRANSFER_ENCODING', '').lower() == 'chunked':
            if uwsgi is None:
                raise RuntimeError('Not running under uwsgi, cannot support '
                                   'chunked encoding')
            if not self.stream:
                _read_chunked(environ)

            else:
                environ['wsgi.input'] = _ChunkedStream()

        return self.app(environ, start_response)