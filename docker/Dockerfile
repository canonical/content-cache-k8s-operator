FROM ubuntu:latest

ENV LANG C.UTF-8
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -qy update && \
    apt-get -qy dist-upgrade --no-install-recommends && \
    apt-get -qy install --no-install-recommends nginx && \
    apt-get -qy clean && \
    rm -f /var/lib/apt/lists/*_*

COPY files/nginx-logging-format.conf /etc/nginx/conf.d/nginx-logging-format.conf

WORKDIR /srv/content-cache

CMD ["nginx", "-g", "daemon off;"]

EXPOSE 80
