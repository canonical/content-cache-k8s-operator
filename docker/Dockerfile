FROM ubuntu:focal

# We use "set -o pipefail"
SHELL ["/bin/bash", "-c"]

ENV LANG C.UTF-8
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -qy update && \
    apt-get -qy dist-upgrade --no-install-recommends && \
    apt-get -qy install --no-install-recommends nginx && \
    apt-get -qy clean && \
    rm -f /var/lib/apt/lists/*_*

RUN rm -f /etc/nginx/sites-enabled/*

WORKDIR /srv/content-cache

# COPY nginx-logging-format.conf /etc/nginx/conf.d/nginx-logging-format.conf
# COPY nginx.conf /etc/nginx/conf.d/default.conf

CMD ["/usr/sbin/nginx", "-g", "daemon off;"]
