#!/bin/sh

uwsgi --mount /=wsgi:application --http-socket=0.0.0.0:8000 \
      --http-chunked-input --py-autoreload=1
