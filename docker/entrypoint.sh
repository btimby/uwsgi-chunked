#!/bin/sh

uwsgi --mount=/buffer=wsgi:buffer --mount=/stream=wsgi:stream \
      --http-socket=0.0.0.0:8000 --http-chunked-input --py-autoreload=1
