import os
import subprocess
import time
import socket
from http import client
from urllib.parse import urlparse, urlencode
from unittest import TestCase, mock

from uwsgi_chunked import chunked


TEST_PORT = int(os.getenv('TEST_PORT', '8000'))
TEST_URL = os.getenv('TEST_URL', f'http://localhost:{TEST_PORT}/')
UWSGI_CMD = [
    'uwsgi', '--mount=/buffer=wsgi:buffer', '--mount=/stream=wsgi:stream',
    f'--http-socket=127.0.0.1:{TEST_PORT}', '--http-chunked-input',
]


def _wait_for_port(port, host='127.0.0.1', timeout=2.0):
    "Try to open a connection until it succeeds"
    start = time.time()
    while True:
        if time.time() - start > timeout:
            raise TimeoutError()

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((host, port))
            return

        except:
            time.sleep(0.01)
            continue

        finally:
            s.close()


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


class ChunkedStreamTestCase(TestCase):
    def test_read_bufferred(self):
        "Ensure read returns the number of bytes asked for."
        mock_read = mock.MagicMock()
        mock_read.side_effect = [
            b'AAAAAAAAAABBBBB',
            b'BBBBBCCCCCCCCCC',
            TimeoutError(),
            b'DDDDDDDDDDEEEEE',
            b'EEEEEFFFFFFFFFF',
            b'',
        ]
        stream = chunked._ChunkedStream(reader=mock_read)
        self.assertEqual(b'A' * 10, stream.read(10))
        self.assertEqual(b'B' * 10, stream.read(10))
        self.assertEqual(b'C' * 10, stream.read(10))
        self.assertEqual(b'D' * 10, stream.read(10))
        self.assertEqual(b'E' * 10, stream.read(10))
        self.assertEqual(b'F' * 10, stream.read(10))
        self.assertIsNone(stream.read())

    def test_read_short(self):
        mock_read = mock.MagicMock()
        mock_read.side_effect = [
            b'AAAAAAAAAA',
            b'',
        ]
        stream = chunked._ChunkedStream(reader=mock_read)
        self.assertEqual(b'A' * 10, stream.read(100))


class UWSGITestCase(TestCase):
    "Test buffering mode."

    PATH = '/buffer'

    def setUp(self):
        urlp = urlparse(TEST_URL)
        self.client = client.HTTPConnection(urlp.hostname, urlp.port)

    def tearDown(self):
        self.client.close()

    @classmethod
    def setUpClass(cls):
        cls._proc = subprocess.Popen(
            UWSGI_CMD, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        _wait_for_port(TEST_PORT)

    @classmethod
    def tearDownClass(cls):
        cls._proc.kill()
        cls._proc.wait()

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
