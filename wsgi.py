from urllib.parse import parse_qs
from uwsgi_chunked import Chunked


def hello_world(environ, start_response):
    "A simple wsgi application."
    data = environ['wsgi.input'].read()
    print('data:', data)
    post = parse_qs(data)
    whom = post.get(b'whom', [b'stranger'])[0]
    write = start_response('200 OK', [('Content-Type', 'text/html')])
    return[b'Hello %b!\n' % whom]


application = Chunked(hello_world)
