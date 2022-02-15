import os
import subprocess
import time
import socket
from http import client
from urllib.parse import urlparse, urlencode
from unittest import TestCase, mock

from uwsgi_chunked import chunked


TEST_OUTPUT = os.getenv('TEST_OUTPUT', '').lower() == 'on'
UWSGI_CMD = [
    'uwsgi',
    '--mount=/=docker.app.wsgi:app',
     '--http-chunked-input',
]


def _free_port():
    "Find a free port by binding to 0 and checking what the kernel assigns."
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    try:
        return s.getsockname()[1]

    finally:
        s.close()


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

        except socket.error:
            time.sleep(0.01)
            continue

        finally:
            s.close()


def _encode_chunk(s):
    "Encode a single chunk."
    return b'\r\n'.join([hex(len(s))[2:].encode(), s.encode()])


def _encode_chunked(s):
    "Ensure string spans multiple chunks."
    return b'\r\n'.join([
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
        self.assertEqual(b'', stream.read())

    def test_read_short(self):
        mock_read = mock.MagicMock()
        mock_read.side_effect = [
            b'AAAAAAAAAA',
            b'',
        ]
        stream = chunked._ChunkedStream(reader=mock_read)
        self.assertEqual(b'A' * 10, stream.read(100))
        self.assertEqual(b'', stream.read())

    def test_read_all(self):
        mock_read = mock.MagicMock()
        mock_read.side_effect = [
            b'AAAAAAAAAA',
            b'AAAAAAAAAA',
            b''
        ]
        stream = chunked._ChunkedStream(reader=mock_read)
        self.assertEqual(b'A' * 20, stream.read())


class UWSGITestCase(TestCase):
    "Test buffering mode."

    ENV = {'STREAM': 'off'}

    def setUp(self):
        urlp = urlparse(self.test_url)
        self.client = client.HTTPConnection(urlp.hostname, urlp.port)

    def tearDown(self):
        self.client.close()

    @classmethod
    def setUpClass(cls):
        env = os.environ.copy()
        env.update(cls.ENV)
        kwargs = {
            'env': env,
        }
        if not TEST_OUTPUT:
            kwargs.update({
                'stdout': subprocess.DEVNULL,
                'stderr': subprocess.DEVNULL,
            })
        free_port = _free_port()
        cmd = UWSGI_CMD + [f'--http-socket=127.0.0.1:{free_port}']
        cls._proc = subprocess.Popen(cmd, **kwargs)
        _wait_for_port(free_port)
        cls.test_url = f'http://localhost:{free_port}/'

    @classmethod
    def tearDownClass(cls):
        cls._proc.kill()
        cls._proc.wait()

    def test_get(self):
        "Normal GET request."
        self.client.request('GET', '/')
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
        self.client.request('POST', '/', params, headers)
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
        self.client.request('POST', '/', params, headers)
        r = self.client.getresponse()
        self.assertEqual(200, r.status)
        self.assertEqual(b'Hello friend!\n', r.read())

    def test_slow(self):
        "Test slow sending."
        params = _encode_chunked(urlencode({ 'whom': 'friend' }))
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Transfer-Encoding': 'chunked',
        }

        def body_gen():
            for chunk in params.split(b'\r\n'):
                yield chunk + b'\r\n'
                time.sleep(1.0)

        self.client.request('POST', '/', body_gen(), headers)
        r = self.client.getresponse()
        self.assertEqual(200, r.status)
        self.assertEqual(b'Hello friend!\n', r.read())


class StreamTestCase(UWSGITestCase):
    "Test stream mode."

    ENV = {'STREAM': 'on'}
