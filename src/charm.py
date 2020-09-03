#!/usr/bin/env python3

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

CONTAINER_PORT = 80
REQUIRED_JUJU_CONFIGS = ['image_path', 'site', 'backends']


class CharmK8SContentCacheCharm(CharmBase):
    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)

        self.framework.observe(self.on.start, self._on_start)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.leader_elected, self._on_leader_elected)
        self.framework.observe(self.on.upgrade_charm, self._on_upgrade_charm)

        self._stored.set_default(things=[])

    def _on_start(self, event) -> None:
        self.model.unit.status = ActiveStatus("Started")

    def _on_config_changed(self, event) -> None:
        if not self.model.unit.is_leader():
            self.unit.status = ActiveStatus()
            return
        self.model.unit.status = MaintenanceStatus("Configuring pod (config-changed)")

        current = self.model.config["thing"]
        if current not in self._stored.things:
            logger.debug("found a new thing: %r", current)
            self._stored.things.append(current)

        self.configure_pod(event)

    def _on_leader_elected(self, event) -> None:
        if not self.model.unit.is_leader():
            self.unit.status = ActiveStatus()
            return
        self.model.unit.status = MaintenanceStatus("Configuring pod (leader-elected)")
        self.configure_pod(event)

    def _on_upgrade_charm(self, event) -> None:
        if not self.model.unit.is_leader():
            self.unit.status = ActiveStatus()
            return
        self.model.unit.status = MaintenanceStatus("Configuring pod (upgrade-charm)")
        self.configure_pod(event)

    def configure_pod(self, event) -> None:
        if not self.model.unit.is_leader():
            return

        missing = self._missing_charm_configs()
        if missing:
            self.unit.status = BlockedStatus("Required config(s) empty: {}".format(", ".join(sorted(missing))))
            return

        self.unit.status = MaintenanceStatus("Assembling pod spec")
        pod_spec = self._make_pod_spec()

        self.unit.status = MaintenanceStatus("Setting pod spec")
        self.model.pod.set_spec(pod_spec)

        self.unit.status = ActiveStatus()

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
                            'mountPath': '/nginx-cache',
                            'emptyDir': {'medium': 'Memory', 'emptyDir': config['cache_size']},
                        }
                    ],
                }
            ],
        }

        return pod_spec

    def _make_pod_config(self) -> dict:
        # config = self.model.config
        pod_config = {
            'TEST_CONFIG': 'false',
        }

        return pod_config

    def _missing_charm_configs(self) -> list:
        config = self.model.config
        missing = []

        missing.extend([setting for setting in REQUIRED_JUJU_CONFIGS if not config[setting]])

        return sorted(list(set(missing)))


if __name__ == "__main__":  # pragma: no cover
    main(CharmK8SContentCacheCharm)
