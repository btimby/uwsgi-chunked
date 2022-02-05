import os
from http import client
from urllib.parse import urlparse, urlencode
from unittest import TestCase


TEST_URL = os.getenv('TEST_URL', 'http://localhost:8000/')


def _encode_chunked(s):
    return '\r\n'.join([hex(len(s))[2:], s, '0', ''])


class TestUWSGIChunkedTestCase(TestCase):
    def setUp(self):
        urlp = urlparse(TEST_URL)
        self.client = client.HTTPConnection(urlp.hostname, urlp.port)

    def tearDown(self):
        self.client.close()

    def test_get(self):
        self.client.request('GET', '/')
        r = self.client.getresponse()
        self.assertEqual(200, r.status)
        self.assertEqual(b'Hello stranger!\n', r.read())

    def test_urlencoded(self):
        params = urlencode({ 'whom': 'friend' })
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Content-Length': str(len(params))
        }
        self.client.request('POST', '/', params, headers)
        r = self.client.getresponse()
        self.assertEqual(200, r.status)
        self.assertEqual(b'Hello friend!\n', r.read())

    def test_chunked(self):
        params = _encode_chunked(urlencode({ 'whom': 'friend' }))
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Transfer-Encoding': 'chunked',
        }
        self.client.request('POST', '/', params, headers)
        r = self.client.getresponse()
        self.assertEqual(200, r.status)
        self.assertEqual(b'Hello friend!\n', r.read())
