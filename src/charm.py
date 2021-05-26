#!/usr/bin/env python3

# Copyright (C) 2020 Canonical Ltd.
# See LICENSE file for licensing details.

import hashlib
import logging
from urllib.parse import urlparse

from charms.nginx_ingress_integrator.v0.ingress import IngressRequires
from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import (
    ActiveStatus,
    BlockedStatus,
    MaintenanceStatus,
    WaitingStatus,
)

logger = logging.getLogger(__name__)

CACHE_PATH = '/var/lib/nginx/proxy/cache'
CONTAINER_NAME = 'content-cache'
CONTAINER_PORT = 80
REQUIRED_JUJU_CONFIGS = ['site', 'backend']


class ContentCacheCharm(CharmBase):
    """Charm the service."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)

        self.framework.observe(self.on.start, self._on_start)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.upgrade_charm, self._on_upgrade_charm)

        self.framework.observe(self.on.content_cache_pebble_ready, self._on_content_cache_pebble_ready)
        self._stored.set_default(content_cache_pebble_ready=False)

        self.ingress = IngressRequires(self, self._make_ingress_config()[0])

    def _on_content_cache_pebble_ready(self, event) -> None:
        """Configure/set up pod."""
        msg = 'Configuring pod (content-cache-pebble-ready)'
        logger.info(msg)
        self.model.unit.status = MaintenanceStatus(msg)
        self._stored.content_cache_pebble_ready = True
        self.configure_pod(event)

    def _on_start(self, event) -> None:
        """Handle pod started."""
        logger.info('Starting pod (start)')
        self.model.unit.status = ActiveStatus('Started')

    def _on_config_changed(self, event) -> None:
        """Configure/set up pod."""
        msg = 'Configuring pod (config-changed)'
        logger.info(msg)
        self.model.unit.status = MaintenanceStatus(msg)
        self.configure_pod(event)

    def _on_upgrade_charm(self, event) -> None:
        """Configure/set up pod."""
        msg = 'Configuring pod (upgrade-charm)'
        logger.info(msg)
        self.model.unit.status = MaintenanceStatus(msg)
        self.configure_pod(event)

    def configure_pod(self, event) -> None:
        """Assemble both K8s ingress and pod spec and apply."""
        missing = self._missing_charm_configs()
        if missing:
            msg = 'Required config(s) empty: {}'.format(', '.join(sorted(missing)))
            logger.warning(msg)
            self.unit.status = BlockedStatus(msg)
            return

        pebble_config = self._make_pebble_config()
        if not self._stored.content_cache_pebble_ready or not pebble_config:
            self.unit.status = WaitingStatus('Waiting for pebble')
            event.defer()
            return

        msg = 'Assembling K8s ingress spec'
        logger.info(msg)
        self.unit.status = MaintenanceStatus(msg)
        self.ingress.update_config(self._make_ingress_config()[0])

        container = self.unit.get_container(CONTAINER_NAME)
        env_config = self._make_env_config()

        msg = 'Updating Nginx site config'
        logger.info(msg)
        self.unit.status = MaintenanceStatus(msg)
        container.make_dir(env_config['NGINX_CACHE_PATH'], make_parents=True)
        with open('files/nginx-logging-format.conf', 'r') as f:
            container.push('/etc/nginx/conf.d/nginx-logging-format.conf', f)
        with open('templates/nginx_cfg.tmpl', 'r') as f:
            content = f.read()
            content = content.format(
                JUJU_POD_NAME=env_config['JUJU_POD_NAME'],
                JUJU_POD_NAMESPACE=env_config['JUJU_POD_NAMESPACE'],
                NGINX_BACKEND=env_config['NGINX_BACKEND'],
                NGINX_BACKEND_SITE_NAME=env_config['NGINX_BACKEND_SITE_NAME'],
                NGINX_CACHE_INACTIVE_TIME=env_config['NGINX_CACHE_INACTIVE_TIME'],
                NGINX_CACHE_MAX_SIZE=env_config['NGINX_CACHE_MAX_SIZE'],
                NGINX_CACHE_PATH=env_config['NGINX_CACHE_PATH'],
                NGINX_CACHE_USE_STALE=env_config['NGINX_CACHE_USE_STALE'],
                NGINX_CACHE_VALID=env_config['NGINX_CACHE_VALID'],
                NGINX_CLIENT_MAX_BODY_SIZE=env_config['NGINX_CLIENT_MAX_BODY_SIZE'],
                NGINX_KEYS_ZONE=env_config['NGINX_KEYS_ZONE'],
                NGINX_SITE_NAME=env_config['NGINX_SITE_NAME'],
            )
            container.push('/etc/nginx/sites-available/default', content)

        msg = 'Assembling pebble layer config'
        logger.info(msg)
        self.unit.status = MaintenanceStatus(msg)
        services = container.get_plan().to_dict().get('services', {})
        if services != pebble_config["services"]:
            self.unit.status = MaintenanceStatus('Adding config layer to Pebble')
            # Add intial Pebble config layer using the Pebble API
            container.add_layer(CONTAINER_NAME, pebble_config, combine=True)
            self.unit.status = MaintenanceStatus('Restarting content-cache')
            service = container.get_service(CONTAINER_NAME)
            if service.is_running():
                container.stop(CONTAINER_NAME)
            container.start(CONTAINER_NAME)

        msg = 'Done applying updated pod spec'
        logger.info(msg)
        self.unit.status = ActiveStatus('Ready')

    def _generate_keys_zone(self, name):
        """Generate hashed name to be used by Nginx's key zone."""
        return '{}-cache'.format(hashlib.md5(name.encode('UTF-8')).hexdigest()[0:12])

    def _make_ingress_config(self) -> list:
        """Return an assembled K8s ingress."""
        config = self.model.config

        ingress = {
            'service-hostname': 'mysite.local',
            'service-name': self.app.name,
            'service-port': CONTAINER_PORT,
        }

        site = config.get('site')
        if site:
            ingress['service-hostname'] = site

        client_max_body_size = config.get('client_max_body_size')
        if client_max_body_size:
            ingress['max-body-size'] = client_max_body_size

        tls_secret_name = config.get('tls_secret_name')
        if tls_secret_name:
            ingress['tls-secret-name'] = tls_secret_name

        return [ingress]

    def _make_pebble_config(self) -> dict:
        """Generate our pebble config layer."""
        env_config = self._make_env_config()
        pebble_config = {
            "summary": "content-cache layer",
            "description": "Pebble config layer for content-cache",
            "services": {
                "content-cache": {
                    "override": "replace",
                    "summary": "content-cache",
                    "command": "/usr/sbin/nginx -g 'daemon off;'",
                    "startup": "false",
                    "environment": env_config,
                },
            },
        }
        return pebble_config

    def _make_env_config(self) -> dict:
        """Return dict to be used as pod spec's envConfig."""
        config = self.model.config

        backend = config['backend']
        backend_site_name = config.get('backend_site_name')
        if not backend_site_name:
            backend_site_name = urlparse(backend).hostname

        client_max_body_size = '1m'
        if config.get('client_max_body_size'):
            client_max_body_size = config.get('client_max_body_size')

        pod_config = {
            'NGINX_BACKEND': backend,
            'NGINX_BACKEND_SITE_NAME': backend_site_name,
            'NGINX_CACHE_INACTIVE_TIME': config.get('cache_inactive_time', '10m'),
            'NGINX_CACHE_MAX_SIZE': config.get('cache_max_size', '10G'),
            'NGINX_CACHE_PATH': CACHE_PATH,
            'NGINX_CACHE_USE_STALE': config['cache_use_stale'],
            'NGINX_CACHE_VALID': config['cache_valid'],
            'NGINX_CLIENT_MAX_BODY_SIZE': client_max_body_size,
            'NGINX_KEYS_ZONE': self._generate_keys_zone(config['site']),
            'NGINX_SITE_NAME': config['site'],
        }

        # https://bugs.launchpad.net/juju/+bug/1894782
        juju_env_config = {
            # "JUJU_NODE_NAME": "spec.nodeName",
            "JUJU_POD_NAME": self.unit.name,
            "JUJU_POD_NAMESPACE": self.model.name,
            # "JUJU_POD_IP": "status.podIP",
            "JUJU_POD_SERVICE_ACCOUNT": self.app.name,
        }
        pod_config.update(juju_env_config)

        return pod_config

    def _missing_charm_configs(self) -> list:
        """Check and return list of required but missing configs."""
        config = self.model.config
        missing = [setting for setting in REQUIRED_JUJU_CONFIGS if setting not in config or not config[setting]]

        return sorted(missing)


if __name__ == '__main__':  # pragma: no cover
    main(ContentCacheCharm, use_juju_for_storage=True)
