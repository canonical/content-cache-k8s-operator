# Copyright (C) 2020 Canonical Ltd.
# See LICENSE file for licensing details.

import copy
import unittest
from unittest import mock

from ops.model import (
    ActiveStatus,
    BlockedStatus,
    MaintenanceStatus,
)
from ops.testing import Harness
from charm import ContentCacheCharm

BASE_CONFIG = {
    'site': 'mysite.local',
    'backend': 'http://mybackend.local:80',
    'cache_max_size': '10G',
    'cache_use_stale': 'error timeout updating http_500 http_502 http_503 http_504',
    'cache_valid': '200 1h',
}
CACHE_PATH = '/var/lib/nginx/proxy/cache'
CONTAINER_NAME = 'content-cache'
CONTAINER_PORT = 80
JUJU_ENV_CONFIG = {
    'JUJU_POD_NAME': 'content-cache-k8s/0',
    'JUJU_POD_NAMESPACE': None,
    'JUJU_POD_SERVICE_ACCOUNT': 'content-cache-k8s',
}
INGRESS_CONFIG = {
    'service-hostname': 'mysite.local',
    'service-name': 'content-cache-k8s',
    'service-port': CONTAINER_PORT,
}
PEBBLE_CONFIG = {
    'summary': 'content-cache layer',
    'description': 'Pebble config layer for content-cache',
    'services': {
        CONTAINER_NAME: {
            'override': 'replace',
            'summary': 'content-cache',
            'command': "/usr/sbin/nginx -g 'daemon off;'",
            "startup": 'false',
            'environment': '',
        },
    },
}


class TestCharm(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.harness = Harness(ContentCacheCharm)

    def tearDown(self):
        # starting from ops 0.8, we also need to do:
        self.addCleanup(self.harness.cleanup)

    @mock.patch('charm.ContentCacheCharm.configure_pod')
    def test_on_content_cache_pebble_ready(self, configure_pod):
        """Test on_content_cache_pebble_ready, ensure configure_pod is called just once."""
        harness = self.harness
        action_event = mock.Mock()

        harness.disable_hooks()
        harness.begin()
        harness.charm._on_content_cache_pebble_ready(action_event)
        config = copy.deepcopy(BASE_CONFIG)
        harness.update_config(config)
        self.assertEqual(harness.charm.unit.status, MaintenanceStatus('Configuring pod (content-cache-pebble-ready)'))
        configure_pod.assert_called_once()

    def test_on_start(self):
        """Test on_start, nothing but setting ActiveStatus."""
        harness = self.harness
        action_event = mock.Mock()

        harness.begin()
        harness.charm._on_start(action_event)
        self.assertEqual(harness.charm.unit.status, ActiveStatus('Started'))

    @mock.patch('charm.ContentCacheCharm.configure_pod')
    def test_on_config_changed(self, configure_pod):
        """Test on_config_changed, ensure configure_pod is called just once."""
        harness = self.harness

        harness.begin()
        config = copy.deepcopy(BASE_CONFIG)
        harness.update_config(config)
        self.assertEqual(harness.charm.unit.status, MaintenanceStatus('Configuring pod (config-changed)'))
        configure_pod.assert_called_once()

    @mock.patch('charm.ContentCacheCharm.configure_pod')
    def test_on_upgrade_charm(self, configure_pod):
        """Test on_upgrade_charm, ensure configure_pod is called just once."""
        harness = self.harness

        harness.begin()
        harness.charm.on.upgrade_charm.emit()
        self.assertEqual(harness.charm.unit.status, MaintenanceStatus('Configuring pod (upgrade-charm)'))
        configure_pod.assert_called_once()

    @mock.patch('charm.ContentCacheCharm._make_pebble_config')
    @mock.patch('ops.model.Container.add_layer')
    @mock.patch('ops.model.Container.get_service')
    @mock.patch('ops.model.Container.make_dir')
    @mock.patch('ops.model.Container.push')
    @mock.patch('ops.model.Container.start')
    @mock.patch('ops.model.Container.stop')
    def test_configure_pod(self, stop, start, push, make_dir, get_service, add_layer, make_pebble_config):
        """Test configure_pod, ensure make_pod_spec is called and the generated pod spec is correct."""
        harness = self.harness

        harness.begin()
        harness.charm._stored.content_cache_pebble_ready = True
        config = copy.deepcopy(BASE_CONFIG)
        harness.update_config(config)
        make_pebble_config.assert_called_once()
        add_layer.assert_called_once()
        get_service.assert_called_once()
        stop.assert_called_once()
        start.assert_called_once()
        self.assertEqual(harness.charm.unit.status, ActiveStatus('Ready'))

    @mock.patch('charm.ContentCacheCharm._make_pebble_config')
    @mock.patch('ops.model.Container.add_layer')
    @mock.patch('ops.model.Container.get_service')
    @mock.patch('ops.model.Container.make_dir')
    @mock.patch('ops.model.Container.push')
    @mock.patch('ops.model.Container.start')
    @mock.patch('ops.model.Container.stop')
    def test_configure_pod_container_not_running(
        self, stop, start, push, make_dir, get_service, add_layer, make_pebble_config
    ):
        """Test configure_pod, ensure make_pod_spec is called and the generated pod spec is correct."""
        harness = self.harness

        harness.begin()
        harness.charm._stored.content_cache_pebble_ready = True
        config = copy.deepcopy(BASE_CONFIG)
        harness.update_config(config)
        make_pebble_config.assert_called_once()
        get_service.return_value.is_running.return_value = False
        harness.update_config(config)
        stop.assert_called_once()

    @mock.patch('charm.ContentCacheCharm._make_pebble_config')
    @mock.patch('ops.model.Container.add_layer')
    @mock.patch('ops.model.Container.get_service')
    @mock.patch('ops.model.Container.make_dir')
    @mock.patch('ops.model.Container.push')
    @mock.patch('ops.model.Container.start')
    @mock.patch('ops.model.Container.stop')
    def test_configure_pod_pebble_services_already_configured(
        self, stop, start, push, make_dir, get_service, add_layer, make_pebble_config
    ):
        """Test configure_pod, ensure make_pod_spec is called and the generated pod spec is correct."""
        harness = self.harness

        harness.begin()
        harness.charm._stored.content_cache_pebble_ready = True
        config = copy.deepcopy(BASE_CONFIG)
        make_pebble_config.return_value = {'services': {}}
        harness.update_config(config)
        make_pebble_config.assert_called_once()
        add_layer.assert_not_called()
        self.assertEqual(harness.charm.unit.status, ActiveStatus('Ready'))

    @mock.patch('charm.ContentCacheCharm._make_pebble_config')
    def test_configure_pod_missing_configs(self, make_pebble_config):
        """Test configure_pod, missing configs so ensure make_pod_spec is not called and no pod spec set."""
        harness = self.harness

        harness.begin()

        config = copy.deepcopy(BASE_CONFIG)
        config['site'] = None
        harness.update_config(config)
        make_pebble_config.assert_not_called()
        self.assertEqual(harness.charm.unit.status, BlockedStatus('Required config(s) empty: site'))
        self.assertEqual(harness.get_pod_spec(), None)

    def test_generate_keys_zone(self):
        """Test generating hashed name for Nginx's cache key zone."""
        harness = self.harness

        harness.disable_hooks()
        harness.begin()

        expected = '39c631ffb52d-cache'
        self.assertEqual(harness.charm._generate_keys_zone('mysite.local'), expected)
        expected = '8b79f9e4b3e8-cache'
        self.assertEqual(harness.charm._generate_keys_zone('my-really-really-really-long-site-name.local'), expected)
        expected = 'd41d8cd98f00-cache'
        self.assertEqual(harness.charm._generate_keys_zone(''), expected)

    def test_make_ingress_config(self):
        """Test generation ingress config and ensure it is correct."""
        harness = self.harness

        harness.disable_hooks()
        harness.begin()

        config = copy.deepcopy(BASE_CONFIG)
        harness.update_config(config)
        expected = copy.deepcopy(INGRESS_CONFIG)
        self.assertEqual(harness.charm._make_ingress_config(), expected)

    def test_make_ingress_config_client_max_body_size(self):
        """Test generation ingress config overriding client_max_body_size and ensure it is correct."""
        harness = self.harness

        harness.disable_hooks()
        harness.begin()

        config = copy.deepcopy(BASE_CONFIG)
        config['client_max_body_size'] = '50m'
        harness.update_config(config)
        expected = copy.deepcopy(INGRESS_CONFIG)
        expected['max-body-size'] = '50m'
        self.assertEqual(harness.charm._make_ingress_config(), expected)

    def test_make_ingress_config_tls_secret(self):
        """Test generation ingress config setting tls_secret_name and ensure it is correct."""
        harness = self.harness

        harness.disable_hooks()
        harness.begin()

        config = copy.deepcopy(BASE_CONFIG)
        config['tls_secret_name'] = 'mysite-com-tls'
        harness.update_config(config, unset=['client_max_body_size'])
        expected = copy.deepcopy(INGRESS_CONFIG)
        expected['tls-secret-name'] = 'mysite-com-tls'
        self.assertEqual(harness.charm._make_ingress_config(), expected)

    def test_make_pebble_config(self):
        """Test make_pebble_config, ensure correct."""
        harness = self.harness

        harness.begin()

        config = copy.deepcopy(BASE_CONFIG)
        harness.update_config(config)
        expected = copy.deepcopy(PEBBLE_CONFIG)
        expected['services']['content-cache']['environment'] = harness.charm._make_env_config()
        self.assertEqual(harness.charm._make_pebble_config(), expected)

    def test_make_env_config(self):
        """Test make_env_config, ensure envConfig returned is correct."""
        harness = self.harness

        harness.disable_hooks()
        harness.begin()

        config = copy.deepcopy(BASE_CONFIG)
        harness.update_config(config)
        expected = {
            'NGINX_BACKEND': 'http://mybackend.local:80',
            'NGINX_BACKEND_SITE_NAME': 'mybackend.local',
            'NGINX_CACHE_INACTIVE_TIME': '10m',
            'NGINX_CACHE_MAX_SIZE': '10G',
            'NGINX_CACHE_PATH': CACHE_PATH,
            'NGINX_CACHE_USE_STALE': 'error timeout updating http_500 http_502 http_503 http_504',
            'NGINX_CACHE_VALID': '200 1h',
            'NGINX_CLIENT_MAX_BODY_SIZE': '1m',
            'NGINX_KEYS_ZONE': '39c631ffb52d-cache',
            'NGINX_SITE_NAME': 'mysite.local',
        }
        expected.update(JUJU_ENV_CONFIG)
        self.assertEqual(harness.charm._make_env_config(), expected)

    def test_make_env_config_backend_site_name(self):
        """Test make_env_config with charm config backend_site_config, ensure envConfig returned is correct."""
        harness = self.harness

        harness.disable_hooks()
        harness.begin()

        config = copy.deepcopy(BASE_CONFIG)
        config['backend_site_name'] = 'myoverridebackendsitename.local'
        harness.update_config(config)
        expected = {
            'NGINX_BACKEND': 'http://mybackend.local:80',
            'NGINX_BACKEND_SITE_NAME': 'myoverridebackendsitename.local',
            'NGINX_CACHE_INACTIVE_TIME': '10m',
            'NGINX_CACHE_MAX_SIZE': '10G',
            'NGINX_CACHE_PATH': CACHE_PATH,
            'NGINX_CACHE_USE_STALE': 'error timeout updating http_500 http_502 http_503 http_504',
            'NGINX_CACHE_VALID': '200 1h',
            'NGINX_CLIENT_MAX_BODY_SIZE': '1m',
            'NGINX_KEYS_ZONE': '39c631ffb52d-cache',
            'NGINX_SITE_NAME': 'mysite.local',
        }
        expected.update(JUJU_ENV_CONFIG)
        self.assertEqual(harness.charm._make_env_config(), expected)

    def test_make_env_config_client_max_body_size(self):
        """Test make_env_config with charm config client_max_body_size, ensure envConfig returned is correct."""
        harness = self.harness

        harness.disable_hooks()
        harness.begin()

        config = copy.deepcopy(BASE_CONFIG)
        config['client_max_body_size'] = '50m'
        harness.update_config(config)
        expected = {
            'NGINX_BACKEND': 'http://mybackend.local:80',
            'NGINX_BACKEND_SITE_NAME': 'mybackend.local',
            'NGINX_CACHE_INACTIVE_TIME': '10m',
            'NGINX_CACHE_MAX_SIZE': '10G',
            'NGINX_CACHE_PATH': CACHE_PATH,
            'NGINX_CACHE_USE_STALE': 'error timeout updating http_500 http_502 http_503 http_504',
            'NGINX_CACHE_VALID': '200 1h',
            'NGINX_CLIENT_MAX_BODY_SIZE': '50m',
            'NGINX_KEYS_ZONE': '39c631ffb52d-cache',
            'NGINX_SITE_NAME': 'mysite.local',
        }
        expected.update(JUJU_ENV_CONFIG)
        self.assertEqual(harness.charm._make_env_config(), expected)

    def test_missing_charm_configs(self):
        """Test missing_charm_config, ensure required configs present and return those missing."""
        harness = self.harness

        harness.disable_hooks()
        harness.begin()

        # All missing, should be sorted.
        config = copy.deepcopy(BASE_CONFIG)
        config.pop('backend')
        config.pop('site')
        harness.update_config(config)
        expected = ['backend', 'site']
        self.assertEqual(harness.charm._missing_charm_configs(), expected)

        # One missing.
        config = copy.deepcopy(BASE_CONFIG)
        config.pop('site')
        harness.update_config(config)
        expected = ['site']
        self.assertEqual(harness.charm._missing_charm_configs(), expected)

        # All set to None, should be sorted.
        config = copy.deepcopy(BASE_CONFIG)
        config['backend'] = None
        config['site'] = None
        harness.update_config(config)
        expected = ['backend', 'site']
        self.assertEqual(harness.charm._missing_charm_configs(), expected)

        # One set to None
        config = copy.deepcopy(BASE_CONFIG)
        config['site'] = None
        harness.update_config(config)
        expected = ['site']
        self.assertEqual(harness.charm._missing_charm_configs(), expected)

        # None missing, all required configs set.
        config = copy.deepcopy(BASE_CONFIG)
        harness.update_config(config)
        expected = []
        self.assertEqual(harness.charm._missing_charm_configs(), expected)
