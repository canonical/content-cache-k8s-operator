#!/bin/sh

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

set -eu

cp /srv/content-cache/files/nginx-logging-format.conf /etc/nginx/conf.d/nginx-logging-format.conf

# https://bugs.launchpad.net/juju/+bug/1894782
JUJU_UNIT=$(basename /var/lib/juju/tools/unit-* | sed -e 's/^unit-//' -e 's/-\([0-9]\+\)$/\/\1/')
export JUJU_UNIT

cat /srv/content-cache/templates/nginx_cfg.tmpl > /etc/nginx/sites-available/default

exec nginx -g 'daemon off;'
