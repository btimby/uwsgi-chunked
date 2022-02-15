"WSGI test application."

import logging

from urllib.parse import parse_qs


LOGGER = logging.getLogger()
LOGGER.addHandler(logging.StreamHandler())
LOGGER.setLevel(logging.DEBUG)


def hello_world(environ, start_response):
    "A simple wsgi application."
    data = environ['wsgi.input'].read()
    post = parse_qs(data)
    whom = post.get(b'whom', [b'stranger'])[0]
    start_response('200 OK', [('Content-Type', 'text/html')])
    return [b'Hello %b!\n' % whom]
