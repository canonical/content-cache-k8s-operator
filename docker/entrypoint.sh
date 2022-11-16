#!/bin/sh

# Copyright (C) 2020 Canonical Ltd.
# See LICENSE file for licensing details.

set -eu

# https://pempek.net/articles/2013/07/08/bash-sh-as-template-engine/
render_template() {
    eval "echo \"$(cat "$1")\""
}

cp /srv/content-cache/mclaren/nginx-logging-format.conf /etc/nginx/conf.d/nginx-logging-format.conf

# https://bugs.launchpad.net/juju/+bug/1894782
JUJU_UNIT=$(basename /var/lib/juju/tools/unit-* | sed -e 's/^unit-//' -e 's/-\([0-9]\+\)$/\/\1/')
export JUJU_UNIT

render_template /srv/content-cache/templates/nginx_cfg.tmpl > /etc/nginx/sites-available/default

# Run the real command
exec "$@"
