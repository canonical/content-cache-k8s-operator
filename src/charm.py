#!/usr/bin/env python3

import logging

from ops.charm import CharmBase
from ops.main import main
from ops.model import (
    ActiveStatus,
    MaintenanceStatus,
)

logger = logging.getLogger(__name__)

CONTAINER_PORT = 80


class CharmK8SContentCacheCharm(CharmBase):
    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.start, self.on_start)
        self.framework.observe(self.on.config_changed, self.on_config_changed)
        self.framework.observe(self.on.leader_elected, self.on_leader_elected)
        self.framework.observe(self.on.upgrade_charm, self.on_upgrade_charm)

    def on_start(self, event) -> None:
        self.model.unit.status = ActiveStatus("Started")

    def on_config_changed(self, event) -> None:
        if not self.model.unit.is_leader():
            return
        self.model.unit.status = MaintenanceStatus("Configuring pod (config-changed)")
        self.configure_pod(self, event)

    def on_leader_elected(self, event) -> None:
        if not self.model.unit.is_leader():
            return
        self.model.unit.status = MaintenanceStatus("Configuring pod (leader-elected)")
        self.configure_pod(self, event)

    def on_upgrade_charm(self, event) -> None:
        if not self.model.unit.is_leader():
            return
        self.model.unit.status = MaintenanceStatus("Configuring pod (upgrade-charm)")
        self.configure_pod(self, event)

    def configure_pod(self, event) -> None:
        if not self.model.unit.is_leader():
            return
        self.unit.status = MaintenanceStatus("Assembling pod spec")
        pod_spec = self._make_pod_spec()

        self.unit.status = MaintenanceStatus("Setting pod spec")
        self.model.pod.set_spec(pod_spec)

        self.unit.status = ActiveStatus()

    def _make_pod_spec(self) -> dict:
        # config = self.model.config
        pod_config = self._make_pod_config()

        pod_spec = {
            'version': 3,  # otherwise resources are ignored
            'containers': [
                {
                    'name': self.app.name,
                    'ports': [{'containerPort': CONTAINER_PORT, 'protocol': 'TCP'}],
                    'envConfig': pod_config,
                    'imagePullPolicy': 'Always',
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


if __name__ == "__main__":  # pragma: no cover
    main(CharmK8SContentCacheCharm)
