FROM ubuntu:latest

ENV LANG C.UTF-8
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -qy update && \
    apt-get -qy dist-upgrade --no-install-recommends && \
    apt-get -qy install --no-install-recommends nginx && \
    apt-get -qy clean && \
    rm -f /var/lib/apt/lists/*_*

RUN mkdir -p /srv/content-cache

COPY entrypoint.sh /srv/content-cache
COPY files /srv/content-cache
COPY templates /srv/content-cache

ENTRYPOINT ["/srv/content-cache/entrypoint.sh"]

CMD ["nginx", "-g", "daemon off;"]

EXPOSE 80
