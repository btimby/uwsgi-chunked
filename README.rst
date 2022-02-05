uwsgi-chunked
=============

WSGI application wrapper that handles ```Transfer-Encoding: chunked```

This library provides a simple wrapper for a wsgi application that uses the
`uwsgi low-level api <https://uwsgi-docs.readthedocs.io/en/latest/Chunked.html>`_
for reading requests that use ```Transfer-Encoding: chunked```.

Installation
------------

.. code-block:: bash

    $ pip install uwsgi_chunked

Usage
-----

Usage with Django is as follows, you should edit the ```wsgi.py``` file
provided in the default Django application.

.. code-block:: python

    """
    WSGI config for myapp project.
    It exposes the WSGI callable as a module-level variable named ``application``.
    For more information on this file, see
    https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/
    """

    import os

    from django.core.wsgi import get_wsgi_application
    from uwsgi_chunked import Chunked

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myapp.settings')

    application = Chunked(get_wsgi_application())

How it works
------------

The ```Chunked``` object looks for a request with
```Transfer-Encoding: chunked``` and reads the request data using the low-level
uwsgi api. It then places the request data into a ```BytesIO``` instance in
```environ['wsgi.input']``` where it is expected. It also sets the
```Content-Length``` header as wsgi requires.
