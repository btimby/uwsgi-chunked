import logging
from io import BytesIO

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())

try:
    import uwsgi

except ImportError:
    uwsgi = None
    LOGGER.warn('Not running under uwsgi')


class Chunked:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        if environ.get('HTTP_TRANSFER_ENCODING', '').lower() == 'chunked':
            if uwsgi is None:
                raise RuntimeError('Not running under uwsgi, cannot support chunked encoding')
            input = BytesIO()
            while True:
                chunk = uwsgi.chunked_read()
                if chunk == b'':
                    break
                input.write(chunk)
            environ['CONTENT_LENGTH'] = str(input.tell())
            environ['wsgi.input'] = input
            input.seek(0)

        return self.app(environ, start_response)
