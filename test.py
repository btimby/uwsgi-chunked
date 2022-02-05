import os
from http import client
from urllib.parse import urlparse, urlencode
from unittest import TestCase

from uwsgi_chunked import chunked


TEST_URL = os.getenv('TEST_URL', 'http://localhost:8000/')


def _encode_chunk(s):
    "Encode a single chunk."
    return '\r\n'.join([hex(len(s))[2:], s])


def _encode_chunked(s):
    "Ensure string spans multiple chunks."
    return '\r\n'.join([
        _encode_chunk(s[0]),
        _encode_chunk(s[1:3]),
        _encode_chunk(s[3:]),
        _encode_chunk(''),
    ])


class UWSGINoneTestCase(TestCase):
    def test_none(self):
        "Ensure that import failure is handled."
        self.assertIsNone(chunked.uwsgi)

    def test_raises(self):
        "Ensure chunking fails outside of uwsgi."
        # Create a fake wsgi application.
        app = chunked.Chunked(lambda x, y: None)
        with self.assertRaises(RuntimeError):
            # Transfer-Encoding header requires uwsgi module.
            list(app({'HTTP_TRANSFER_ENCODING': 'chunked'}, None))


class UWSGITestCase(TestCase):
    "Test buffering mode."

    PATH = '/buffer'

    def setUp(self):
        urlp = urlparse(TEST_URL)
        self.client = client.HTTPConnection(urlp.hostname, urlp.port)

    def tearDown(self):
        self.client.close()

    def test_get(self):
        "Normal GET request."
        self.client.request('GET', self.PATH)
        r = self.client.getresponse()
        self.assertEqual(200, r.status)
        self.assertEqual(b'Hello stranger!\n', r.read())

    def test_urlencoded(self):
        "Normal POST request."
        params = urlencode({ 'whom': 'friend' })
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Content-Length': str(len(params))
        }
        self.client.request('POST', self.PATH, params, headers)
        r = self.client.getresponse()
        self.assertEqual(200, r.status)
        self.assertEqual(b'Hello friend!\n', r.read())

    def test_chunked(self):
        "Chunked POST request."
        params = _encode_chunked(urlencode({ 'whom': 'friend' }))
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Transfer-Encoding': 'chunked',
        }
        self.client.request('POST', self.PATH, params, headers)
        r = self.client.getresponse()
        self.assertEqual(200, r.status)
        self.assertEqual(b'Hello friend!\n', r.read())


class StreamTestCase(UWSGITestCase):
    "Test stream mode."

    PATH = '/stream'
