import unittest
from unittest import mock

from ops.model import (
    ActiveStatus,
    BlockedStatus,
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
        # starting from ops 0.8, we also need to do:
        self.addCleanup(self.harness.cleanup)

    def test_on_start(self):
        harness = self.harness
        action_event = mock.Mock()

        harness.charm._on_start(action_event)
        self.assertEqual(harness.charm.unit.status, ActiveStatus('Started'))

    @mock.patch('charm.CharmK8SContentCacheCharm.configure_pod')
    def test_on_config_changed(self, configure_pod):
        harness = self.harness
        action_event = mock.Mock()

        self.assertEqual(list(harness.charm._stored.things), [])
        harness.update_config({"thing": "foo"})

        harness.disable_hooks()  # we don't want leader-set to fire
        harness.set_leader(True)
        harness.charm._on_config_changed(action_event)
        self.assertEqual(harness.charm.unit.status, MaintenanceStatus('Configuring pod (config-changed)'))
        configure_pod.assert_called_once()

        harness.charm._on_config_changed(action_event)
        self.assertEqual(list(harness.charm._stored.things), ["foo"])

    @mock.patch('charm.CharmK8SContentCacheCharm.configure_pod')
    def test_on_config_changed_not_leader(self, configure_pod):
        harness = self.harness
        action_event = mock.Mock()

        harness.set_leader(False)
        harness.charm._on_config_changed(action_event)
        self.assertNotEqual(harness.charm.unit.status, MaintenanceStatus('Configuring pod (config-changed)'))
        configure_pod.assert_not_called()

    @mock.patch('charm.CharmK8SContentCacheCharm.configure_pod')
    def test_on_leader_elected(self, configure_pod):
        harness = self.harness
        action_event = mock.Mock()

        harness.disable_hooks()  # we don't want leader-set to fire
        harness.set_leader(True)
        harness.charm._on_leader_elected(action_event)
        self.assertEqual(harness.charm.unit.status, MaintenanceStatus('Configuring pod (leader-elected)'))
        configure_pod.assert_called_once()

    @mock.patch('charm.CharmK8SContentCacheCharm.configure_pod')
    def test_on_leader_elected_not_leader(self, configure_pod):
        harness = self.harness
        action_event = mock.Mock()

        harness.set_leader(False)
        harness.charm._on_leader_elected(action_event)
        self.assertNotEqual(harness.charm.unit.status, MaintenanceStatus('Configuring pod (leader-elected)'))
        configure_pod.assert_not_called()

    @mock.patch('charm.CharmK8SContentCacheCharm.configure_pod')
    def test_on_upgrade_charm(self, configure_pod):
        harness = self.harness
        action_event = mock.Mock()

        harness.disable_hooks()  # we don't want leader-set to fire
        harness.set_leader(True)
        harness.charm._on_upgrade_charm(action_event)
        self.assertEqual(harness.charm.unit.status, MaintenanceStatus('Configuring pod (upgrade-charm)'))
        configure_pod.assert_called_once()

    @mock.patch('charm.CharmK8SContentCacheCharm.configure_pod')
    def test_on_upgrade_charm_not_leader(self, configure_pod):
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

        harness.update_config(
            {"image_path": "localhost:32000/myimage:latest", "site": "mysite.local", "backends": "localhost:80"}
        )
        harness.disable_hooks()  # we don't want leader-set to fire
        harness.set_leader(True)
        harness.charm.configure_pod(action_event)
        self.assertEqual(harness.charm.unit.status, ActiveStatus())

        make_pod_spec.assert_called_once()

        pod_spec = harness.charm._make_pod_spec()
        k8s_resources = None
        self.assertEqual(harness.get_pod_spec(), (pod_spec, k8s_resources))

    @mock.patch('charm.CharmK8SContentCacheCharm._make_pod_spec')
    def test_configure_pod_missing_configs(self, make_pod_spec):
        harness = self.harness
        action_event = mock.Mock()

        harness.update_config(
            {"image_path": "localhost:32000/myimage:latest", "site": None, "backends": "localhost:80"}
        )
        harness.disable_hooks()  # we don't want leader-set to fire
        harness.set_leader(True)
        harness.charm.configure_pod(action_event)
        self.assertEqual(harness.charm.unit.status, BlockedStatus("Required config(s) empty: site"))

    @mock.patch('charm.CharmK8SContentCacheCharm._make_pod_spec')
    def test_configure_pod_not_leader(self, make_pod_spec):
        harness = self.harness
        action_event = mock.Mock()

        harness.disable_hooks()  # we don't want leader-set to fire
        harness.set_leader(False)
        harness.charm.configure_pod(action_event)
        make_pod_spec.assert_not_called()

    def test_make_pod_spec(self):
        harness = self.harness

        harness.update_config(
            {"image_path": "localhost:32000/myimage:latest", "site": "mysite.local", "backends": "localhost:80"}
        )
        harness.charm._make_pod_spec()

    def test_make_pod_spec_image_username(self):
        harness = self.harness

        harness.update_config(
            {
                "image_path": "localhost:32000/myimage:latest",
                "image_username": "myuser",
                "image_password": "mypassword",
                "site": "mysite.local",
                "backends": "localhost:80",
            }
        )
        harness.charm._make_pod_spec()

    def test_make_pod_config(self):
        harness = self.harness

        harness.charm._make_pod_config()

    def test_missing_charm_configs(self):
        harness = self.harness

        harness.update_config(
            {"image_path": "localhost:32000/myimage:latest", "site": "mysite.local", "backends": "localhost:80"}
        )
        expected = []
        self.assertEqual(harness.charm._missing_charm_configs(), expected)

        harness.update_config(
            {"image_path": "localhost:32000/myimage:latest", "site": None, "backends": "localhost:80"}
        )
        expected = ["site"]
        self.assertEqual(harness.charm._missing_charm_configs(), expected)

        harness.update_config({"image_path": "localhost:32000/myimage:latest", "site": "", "backends": "localhost:80"})
        expected = ["site"]
        self.assertEqual(harness.charm._missing_charm_configs(), expected)
