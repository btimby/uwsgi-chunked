#!/bin/sh

cd /app
uwsgi --mount=/=wsgi:app --http-socket=0.0.0.0:8000 \
      --http-chunked-input --py-autoreload=1
