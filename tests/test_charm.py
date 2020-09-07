import copy
import unittest
from unittest import mock

from ops.model import (
    ActiveStatus,
    BlockedStatus,
    MaintenanceStatus,
)
from ops.testing import Harness
from charm import CharmK8SContentCacheCharm

BASE_CONFIG = {
    'image_path': 'localhost:32000/myimage:latest',
    'site': 'mysite.local',
    'backends': 'localhost:80',
    'cache_max_size': '10G',
}
CACHE_PATH = '/var/lib/nginx/proxy/cache'
CONTAINER_PORT = 80
CONTAINER_SPEC_TMPL = {
    'name': 'charm-k8s-content-cache',
    'envConfig': None,
    'imageDetails': None,
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
    'volumeConfig': None,
}


class TestCharm(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.harness = Harness(CharmK8SContentCacheCharm)

    def tearDown(self):
        # starting from ops 0.8, we also need to do:
        self.addCleanup(self.harness.cleanup)

    def test_on_start(self):
        harness = self.harness
        action_event = mock.Mock()

        harness.begin()
        harness.charm._on_start(action_event)
        self.assertEqual(harness.charm.unit.status, ActiveStatus('Started'))

    @mock.patch('charm.CharmK8SContentCacheCharm.configure_pod')
    def test_on_config_changed(self, configure_pod):
        harness = self.harness

        # Intentionally before harness.begin() to avoid firing leadership events.
        harness.set_leader(True)
        harness.begin()

        config = copy.deepcopy(BASE_CONFIG)
        harness.update_config(config)
        self.assertEqual(harness.charm.unit.status, MaintenanceStatus('Configuring pod (config-changed)'))
        configure_pod.assert_called_once()

    @mock.patch('charm.CharmK8SContentCacheCharm.configure_pod')
    def test_on_config_changed_not_leader(self, configure_pod):
        harness = self.harness

        # Intentionally before harness.begin() to avoid firing leadership events.
        harness.set_leader(False)
        harness.begin()

        config = copy.deepcopy(BASE_CONFIG)
        harness.update_config(config)
        self.assertNotEqual(harness.charm.unit.status, MaintenanceStatus('Configuring pod (config-changed)'))
        configure_pod.assert_not_called()

    @mock.patch('charm.CharmK8SContentCacheCharm.configure_pod')
    def test_on_leader_elected(self, configure_pod):
        harness = self.harness

        harness.begin()
        # Intentionally after harness.begin() to trigger leadership events.
        harness.set_leader(True)
        self.assertEqual(harness.charm.unit.status, MaintenanceStatus('Configuring pod (leader-elected)'))
        configure_pod.assert_called_once()

    @mock.patch('charm.CharmK8SContentCacheCharm.configure_pod')
    def test_on_leader_elected_not_leader(self, configure_pod):
        harness = self.harness

        harness.begin()
        # Intentionally after harness.begin() to trigger leadership events.
        harness.set_leader(False)
        self.assertNotEqual(harness.charm.unit.status, MaintenanceStatus('Configuring pod (leader-elected)'))
        configure_pod.assert_not_called()

    @mock.patch('charm.CharmK8SContentCacheCharm.configure_pod')
    def test_on_upgrade_charm(self, configure_pod):
        harness = self.harness
        action_event = mock.Mock()

        # Disable hooks and fire them manually as that seems to be the
        # only way to test upgrade-charm.
        harness.disable_hooks()
        harness.set_leader(True)
        harness.begin()

        harness.charm._on_upgrade_charm(action_event)
        self.assertEqual(harness.charm.unit.status, MaintenanceStatus('Configuring pod (upgrade-charm)'))
        configure_pod.assert_called_once()

    @mock.patch('charm.CharmK8SContentCacheCharm.configure_pod')
    def test_on_upgrade_charm_not_leader(self, configure_pod):
        harness = self.harness
        action_event = mock.Mock()

        # Disable hooks and fire them manually as that seems to be the
        # only way to test upgrade-charm.
        harness.disable_hooks()
        harness.set_leader(False)
        harness.begin()

        harness.charm._on_upgrade_charm(action_event)
        self.assertNotEqual(harness.charm.unit.status, MaintenanceStatus('Configuring pod (upgrade-charm)'))
        configure_pod.assert_not_called()

    @mock.patch('charm.CharmK8SContentCacheCharm._make_pod_spec')
    def test_configure_pod(self, make_pod_spec):
        harness = self.harness

        harness.set_leader(True)
        harness.begin()

        config = copy.deepcopy(BASE_CONFIG)
        harness.update_config(config)
        make_pod_spec.assert_called_once()
        self.assertEqual(harness.charm.unit.status, ActiveStatus())
        pod_spec = harness.charm._make_pod_spec()
        k8s_resources = None
        self.assertEqual(harness.get_pod_spec(), (pod_spec, k8s_resources))

    @mock.patch('charm.CharmK8SContentCacheCharm._make_pod_spec')
    def test_configure_pod_missing_configs(self, make_pod_spec):
        harness = self.harness

        harness.set_leader(True)
        harness.begin()

        config = copy.deepcopy(BASE_CONFIG)
        config['site'] = None
        harness.update_config(config)
        make_pod_spec.assert_not_called()
        self.assertEqual(harness.charm.unit.status, BlockedStatus('Required config(s) empty: site'))
        self.assertEqual(harness.get_pod_spec(), None)

    def test_make_pod_spec(self):
        harness = self.harness

        harness.set_leader(True)
        harness.begin()

        config = copy.deepcopy(BASE_CONFIG)
        harness.update_config(config)
        t = copy.deepcopy(CONTAINER_SPEC_TMPL)
        t['envConfig'] = harness.charm._make_pod_config()
        t['imageDetails'] = {'imagePath': 'localhost:32000/myimage:latest'}
        t['volumeConfig'] = [
            {'name': 'cache-volume', 'mountPath': '/var/lib/nginx/proxy/cache', 'emptyDir': {'sizeLimit': '10G'}}
        ]
        k8s_resources = None
        expected = ({'version': 3, 'containers': [t]}, k8s_resources)
        self.assertEqual(harness.get_pod_spec(), expected)

    def test_make_pod_spec_image_username(self):
        harness = self.harness

        harness.set_leader(True)
        harness.begin()

        config = copy.deepcopy(BASE_CONFIG)
        config['image_username'] = 'myuser'
        config['image_password'] = 'mypassword'
        harness.update_config(config)
        t = copy.deepcopy(CONTAINER_SPEC_TMPL)
        t['envConfig'] = harness.charm._make_pod_config()
        t['imageDetails'] = {
            'imagePath': 'localhost:32000/myimage:latest',
            'username': 'myuser',
            'password': 'mypassword',
        }
        t['volumeConfig'] = [
            {'name': 'cache-volume', 'mountPath': '/var/lib/nginx/proxy/cache', 'emptyDir': {'sizeLimit': '10G'}}
        ]
        k8s_resources = None
        expected = ({'version': 3, 'containers': [t]}, k8s_resources)
        self.assertEqual(harness.get_pod_spec(), expected)

    def test_make_pod_spec_cache_max_size(self):
        harness = self.harness

        harness.set_leader(True)
        harness.begin()

        config = copy.deepcopy(BASE_CONFIG)
        config['cache_max_size'] = '201G'
        harness.update_config(config)
        t = copy.deepcopy(CONTAINER_SPEC_TMPL)
        t['envConfig'] = harness.charm._make_pod_config()
        t['imageDetails'] = {'imagePath': 'localhost:32000/myimage:latest'}
        t['volumeConfig'] = [
            {'name': 'cache-volume', 'mountPath': '/var/lib/nginx/proxy/cache', 'emptyDir': {'sizeLimit': '201G'}}
        ]
        k8s_resources = None
        expected = ({'version': 3, 'containers': [t]}, k8s_resources)
        self.assertEqual(harness.get_pod_spec(), expected)

    def test_make_pod_config(self):
        harness = self.harness

        harness.disable_hooks()
        harness.begin()

        config = copy.deepcopy(BASE_CONFIG)
        harness.update_config(config)
        expected = {
            'NGINX_BACKEND': 'localhost:80',
            'NGINX_CACHE_INACTIVE_TIME': '10m',
            'NGINX_CACHE_MAX_SIZE': '10G',
            'NGINX_CACHE_PATH': CACHE_PATH,
            'NGINX_SITE_NAME': 'mysite.local',
        }
        self.assertEqual(harness.charm._make_pod_config(), expected)

    def test_missing_charm_configs(self):
        harness = self.harness

        harness.disable_hooks()
        harness.begin()

        config = copy.deepcopy(BASE_CONFIG)
        harness.update_config(config)
        expected = []
        self.assertEqual(harness.charm._missing_charm_configs(), expected)

        config = copy.deepcopy(BASE_CONFIG)
        config['site'] = None
        harness.update_config(config)
        expected = ['site']
        self.assertEqual(harness.charm._missing_charm_configs(), expected)

        config = copy.deepcopy(BASE_CONFIG)
        config['image_path'] = None
        config['site'] = None
        harness.update_config(config)
        expected = ['image_path', 'site']
        self.assertEqual(harness.charm._missing_charm_configs(), expected)
