#!/usr/bin/env python3

# Copyright (C) 2020 Canonical Ltd.
# See LICENSE file for licensing details.

import hashlib
import logging

from ops.charm import CharmBase
from ops.main import main
from ops.framework import StoredState
from ops.model import (
    ActiveStatus,
    BlockedStatus,
    MaintenanceStatus,
)

logger = logging.getLogger(__name__)

CACHE_PATH = '/var/lib/nginx/proxy/cache'
CONTAINER_PORT = 80
REQUIRED_JUJU_CONFIGS = ['image_path', 'site', 'backend']


class ContentCacheCharm(CharmBase):
    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)

        self.framework.observe(self.on.start, self._on_start)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.leader_elected, self._on_leader_elected)
        self.framework.observe(self.on.upgrade_charm, self._on_upgrade_charm)

        self._stored.set_default()

    def _on_start(self, event) -> None:
        self.model.unit.status = ActiveStatus('Started')

    def _on_config_changed(self, event) -> None:
        if not self.model.unit.is_leader():
            logger.info('Spec changes ignored by non-leader')
            self.unit.status = ActiveStatus('Ready')
            return
        msg = 'Configuring pod (config-changed)'
        logger.info(msg)
        self.model.unit.status = MaintenanceStatus(msg)

        self.configure_pod(event)

    def _on_leader_elected(self, event) -> None:
        msg = 'Configuring pod (leader-elected)'
        logger.info(msg)
        self.model.unit.status = MaintenanceStatus(msg)
        self.configure_pod(event)

    def _on_upgrade_charm(self, event) -> None:
        if not self.model.unit.is_leader():
            logger.info('Spec changes ignored by non-leader')
            self.unit.status = ActiveStatus('Ready')
            return
        msg = 'Configuring pod (upgrade-charm)'
        logger.info(msg)
        self.model.unit.status = MaintenanceStatus(msg)
        self.configure_pod(event)

    def configure_pod(self, event) -> None:
        missing = self._missing_charm_configs()
        if missing:
            msg = 'Required config(s) empty: {}'.format(', '.join(sorted(missing)))
            logger.warning(msg)
            self.unit.status = BlockedStatus(msg)
            return

        msg = 'Assembling K8s ingress spec'
        logger.info(msg)
        self.unit.status = MaintenanceStatus(msg)
        ingress_spec = self._make_k8s_ingress_spec()
        k8s_resources = {'kubernetesResources': {'ingressResources': ingress_spec}}

        msg = 'Assembling pod spec'
        logger.info(msg)
        self.unit.status = MaintenanceStatus(msg)
        pod_spec = self._make_pod_spec()

        msg = 'Setting pod spec'
        logger.info(msg)
        self.unit.status = MaintenanceStatus(msg)
        self.model.pod.set_spec(pod_spec, k8s_resources=k8s_resources)

        msg = 'Done applying updated pod spec'
        logger.info(msg)
        self.unit.status = ActiveStatus('Ready')

    def _generate_keys_zone(self, name):
        return '{}-cache'.format(hashlib.md5(name.encode('UTF-8')).hexdigest()[0:12])

    def _make_k8s_ingress_spec(self) -> list:
        config = self.model.config

        annotations = {}
        ingress = {
            'name': '{}-ingress'.format(self.app.name),
            'spec': {
                'rules': [
                    {
                        'host': config['site'],
                        'http': {
                            'paths': [
                                {'path': '/', 'backend': {'serviceName': self.app.name, 'servicePort': CONTAINER_PORT}}
                            ],
                        },
                    }
                ],
            },
        }

        client_max_body_size = config.get('client_max_body_size')
        if client_max_body_size:
            annotations['nginx.ingress.kubernetes.io/proxy-body-size'] = client_max_body_size

        tls_secret_name = config.get('tls_secret_name')
        if tls_secret_name:
            ingress['spec']['tls'] = [{'hosts': config['site'], 'secretName': tls_secret_name}]
        else:
            annotations['nginx.ingress.kubernetes.io/ssl-redirect'] = 'false'

        if annotations:
            ingress['annotations'] = annotations

        return [ingress]

    def _make_pod_spec(self) -> dict:
        config = self.model.config

        image_details = {
            'imagePath': config['image_path'],
        }
        if config.get('image_username', None):
            image_details.update({'username': config['image_username'], 'password': config['image_password']})

        pod_config = self._make_pod_config()

        pod_spec = {
            'version': 3,  # otherwise resources are ignored
            'containers': [
                {
                    'name': self.app.name,
                    'envConfig': pod_config,
                    'imageDetails': image_details,
                    'imagePullPolicy': 'Always',
                    'kubernetes': {
                        'livenessProbe': {
                            'httpGet': {'path': '/', 'port': CONTAINER_PORT},
                            'initialDelaySeconds': 3,
                            'periodSeconds': 3,
                        },
                        'readinessProbe': {
                            'httpGet': {'path': '/', 'port': CONTAINER_PORT},
                            'initialDelaySeconds': 3,
                            'periodSeconds': 3,
                        },
                    },
                    'ports': [{'containerPort': CONTAINER_PORT, 'protocol': 'TCP'}],
                    'volumeConfig': [
                        {
                            'name': 'cache-volume',
                            'mountPath': CACHE_PATH,
                            'emptyDir': {'sizeLimit': config['cache_max_size']},
                        }
                    ],
                }
            ],
        }

        return pod_spec

    def _make_pod_config(self) -> dict:
        config = self.model.config

        client_max_body_size = '1m'
        if config.get('client_max_body_size', ''):
            client_max_body_size = config.get('client_max_body_size')

        pod_config = {
            'NGINX_BACKEND': config['backend'],
            'NGINX_CACHE_INACTIVE_TIME': config.get('cache_inactive_time', '10m'),
            'NGINX_CACHE_MAX_SIZE': config.get('cache_max_size', '10G'),
            'NGINX_CACHE_PATH': CACHE_PATH,
            'NGINX_CACHE_USE_STALE': config['cache_use_stale'],
            'NGINX_CACHE_VALID': config['cache_valid'],
            'NGINX_CLIENT_MAX_BODY_SIZE': client_max_body_size,
            'NGINX_KEYS_ZONE': self._generate_keys_zone(config['site']),
            'NGINX_SITE_NAME': config['site'],
        }

        return pod_config

    def _missing_charm_configs(self) -> list:
        config = self.model.config
        missing = []

        missing.extend([setting for setting in REQUIRED_JUJU_CONFIGS if not config[setting]])

        return sorted(list(set(missing)))


if __name__ == '__main__':  # pragma: no cover
    main(ContentCacheCharm)
