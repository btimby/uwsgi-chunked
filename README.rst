.. image:: https://coveralls.io/repos/github/btimby/uwsgi-chunked/badge.svg?branch=master
    :target: https://coveralls.io/github/btimby/uwsgi-chunked?branch=master

.. image:: https://github.com/btimby/uwsgi-chunked/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/btimby/uwsgi-chunked/actions

.. image:: https://badge.fury.io/py/uwsgi-chunked.svg
    :target: https://badge.fury.io/py/uwsgi-chunked

uwsgi-chunked
=============

WSGI application wrapper that handles ``Transfer-Encoding: chunked``

This library provides a simple wrapper for a WSGI application that uses the
`uwsgi low-level api <https://uwsgi-docs.readthedocs.io/en/latest/Chunked.html>`_
for reading requests that use ``Transfer-Encoding: chunked``.

In normal operation, it will read the entire request into memory, so if you
expect large requests (like uploads), you should offload these to a proxy such
as nginx, or if your application allows it, use stream mode.

Installation
------------

.. code-block:: bash

    $ pip install uwsgi_chunked

Usage
-----

When you run ``uwsgi``, pass the argument: ``--http-chunked-input``.

Usage with Django is as follows, you should edit the ``wsgi.py`` file
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

To use stream mode, pass the optional keyword argument ``stream=True`` to
``Chunked``. Be careful with stream mode as it does not set the
``Content-Length`` header as required by the WSGI spec.

.. code-block:: python

    application = Chunked(get_wsgi_application(), stream=True)

How it works
------------

The ``Chunked`` object looks for a request with
``Transfer-Encoding: chunked`` and reads the request data using the low-level
uwsgi api. It then places the request data into a ``BytesIO`` instance in
``environ['wsgi.input']`` where it is expected. It also sets the
``Content-Length`` header as WSGI requires. When not using stream mode, the
entire request is read into memory in order to calculate the
``Content-Length`` header.

Development
-----------

Issues and PRs welcome. This is a simple module that has no dependencies
except that it only works when running under ``uwsgi``. When running under
``uwsgi`` a special module is available that provides the necessary api.

You can run the demo application in docker with ``make run``. The demo
application uses auto reloading to detect changes to the python modules.

Tests require the demo application (running under ``uwsgi``) to function.
Therefore, do ``make run`` in one terminal and ``make test`` in another.

You can also test using curl with the ``make curl`` target (while the demo app
is running).
