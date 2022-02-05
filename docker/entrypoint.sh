#!/bin/sh

uwsgi --mount=/clen=wsgi:clen --mount=/stream=wsgi:stream \
      --http-socket=0.0.0.0:8000 --http-chunked-input --py-autoreload=1
