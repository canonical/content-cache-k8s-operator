#!/bin/sh

set -eu

# https://pempek.net/articles/2013/07/08/bash-sh-as-template-engine/
render_template() {
    eval "echo \"$(cat $1)\""
}

cp /srv/content-cache/files/nginx-logging-format.conf /etc/nginx/conf.d/nginx-logging-format.conf

render_template /srv/content-cache/templates/nginx_cfg.tmpl > /etc/nginx/sites-available/default

# Run the real command
exec "$@"
