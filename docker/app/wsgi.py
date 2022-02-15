"WSGI app using streaming."
import os

from .hello_world import hello_world
from uwsgi_chunked import Chunked


STREAM = os.getenv('STREAM', '').lower() == 'on'

app = Chunked(hello_world, stream=STREAM)
