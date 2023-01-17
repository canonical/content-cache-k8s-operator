# Copyright (C) 2020 Canonical Ltd.
# See LICENSE file for licensing details.

FROM ubuntu:jammy

ENV LANG C.UTF-8
ENV DEBIAN_FRONTEND noninteractive

# Don't install recommends to keep image small and avoid nasty surprises
# e.g. rpcbind being pulled in by nrpe.
RUN apt-get -qy update && \
    apt-get -qy install --no-install-recommends nginx-light && \
    apt-get -qy clean && \
    rm -f /var/lib/apt/lists/*

RUN mkdir -p /srv/content-cache

COPY docker/entrypoint.sh /srv/content-cache
COPY files /srv/content-cache/files/
COPY templates /srv/content-cache/templates/

ENTRYPOINT ["/srv/content-cache/entrypoint.sh"]

CMD ["nginx", "-g", "daemon off;"]

EXPOSE 80
