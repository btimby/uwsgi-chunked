FROM python:3-alpine

ADD ./docker/entrypoint.sh /entrypoint.sh
ADD ./docker/app/ /app
ADD ./uwsgi_chunked/chunked.py /app/uwsgi_chunked.py

RUN apk --no-cache add build-base linux-headers && \
    pip3 install uwsgi && \
    chmod +x /entrypoint.sh

WORKDIR /

ENTRYPOINT [ "/entrypoint.sh" ]
