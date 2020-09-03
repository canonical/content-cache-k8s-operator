FROM ubuntu:focal

# We use "set -o pipefail"
SHELL ["/bin/bash", "-c"]

ENV LANG C.UTF-8
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -qy update && \
    apt-get -qy dist-upgrade --no-install-recommends && \
    apt-get -qy install --no-install-recommends nginx && \
    rm -f /var/lib/apt/lists/*_*
