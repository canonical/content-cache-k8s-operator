import unittest
from unittest import mock

from ops.model import (
    ActiveStatus,
    MaintenanceStatus,
)
from ops.testing import Harness
from charm import CharmK8SContentCacheCharm


class TestCharm(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

        self.harness = Harness(CharmK8SContentCacheCharm)
        self.harness.begin()

    def tearDown(self):
        self.harness.cleanup()

    def test_start(self):
        harness = self.harness
        action_event = mock.Mock()
        harness.charm._on_start(action_event)
        self.assertEqual(harness.charm.unit.status, ActiveStatus('Started'))

    @mock.patch('charm.CharmK8SContentCacheCharm.configure_pod')
    def test_config_changed(self, configure_pod):
        harness = self.harness
        action_event = mock.Mock()

        harness.disable_hooks()  # we don't want leader-set to fire
        harness.set_leader(True)
        harness.charm._on_config_changed(action_event)
        self.assertEqual(harness.charm.unit.status, MaintenanceStatus('Configuring pod (config-changed)'))
        configure_pod.assert_called_once()

    @mock.patch('charm.CharmK8SContentCacheCharm.configure_pod')
    def test_config_changed_not_leader(self, configure_pod):
        harness = self.harness
        action_event = mock.Mock()

        harness.set_leader(False)
        harness.charm._on_config_changed(action_event)
        self.assertNotEqual(harness.charm.unit.status, MaintenanceStatus('Configuring pod (config-changed)'))
        configure_pod.assert_not_called()

    @mock.patch('charm.CharmK8SContentCacheCharm.configure_pod')
    def test_leader_elected(self, configure_pod):
        harness = self.harness
        action_event = mock.Mock()

        harness.disable_hooks()  # we don't want leader-set to fire
        harness.set_leader(True)
        harness.charm._on_leader_elected(action_event)
        self.assertEqual(harness.charm.unit.status, MaintenanceStatus('Configuring pod (leader-elected)'))
        configure_pod.assert_called_once()

    @mock.patch('charm.CharmK8SContentCacheCharm.configure_pod')
    def test_leader_elected_not_leader(self, configure_pod):
        harness = self.harness
        action_event = mock.Mock()

        harness.set_leader(False)
        harness.charm._on_leader_elected(action_event)
        self.assertNotEqual(harness.charm.unit.status, MaintenanceStatus('Configuring pod (leader-elected)'))
        configure_pod.assert_not_called()

    @mock.patch('charm.CharmK8SContentCacheCharm.configure_pod')
    def test_upgrade_charm(self, configure_pod):
        harness = self.harness
        action_event = mock.Mock()

        harness.disable_hooks()  # we don't want leader-set to fire
        harness.set_leader(True)
        harness.charm._on_upgrade_charm(action_event)
        self.assertEqual(harness.charm.unit.status, MaintenanceStatus('Configuring pod (upgrade-charm)'))
        configure_pod.assert_called_once()

    @mock.patch('charm.CharmK8SContentCacheCharm.configure_pod')
    def test_upgrade_charm_not_leader(self, configure_pod):
        harness = self.harness
        action_event = mock.Mock()

        harness.set_leader(False)
        harness.charm._on_upgrade_charm(action_event)
        self.assertNotEqual(harness.charm.unit.status, MaintenanceStatus('Configuring pod (upgrade-charm)'))
        configure_pod.assert_not_called()

    @mock.patch('charm.CharmK8SContentCacheCharm._make_pod_spec')
    def test_configure_pod(self, make_pod_spec):
        harness = self.harness
        action_event = mock.Mock()

        harness.disable_hooks()  # we don't want leader-set to fire
        harness.set_leader(True)
        harness.charm.configure_pod(action_event)
        self.assertEqual(harness.charm.unit.status, ActiveStatus())

        make_pod_spec.assert_called_once()

    def test_make_pod_spec(self):
        harness = self.harness
        harness.charm._make_pod_spec()

    def test_make_pod_config(self):
        harness = self.harness
        harness.charm._make_pod_config()
