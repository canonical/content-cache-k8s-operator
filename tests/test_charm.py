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
    """Test the charm"""

    def setUp(self):
        self.maxDiff = None

        self.config = copy.deepcopy(BASE_CONFIG)
        self.harness = Harness(ContentCacheCharm)
        self.harness.begin()

    def tearDown(self):
        # starting from ops 0.8, we also need to do:
        self.addCleanup(self.harness.cleanup)

    @mock.patch('charm.ContentCacheCharm.configure_workload_container')
    def test_on_content_cache_pebble_ready(self, configure_workload_container):
        """Test on_content_cache_pebble_ready, ensure configure_workload_container is called just once."""
        config = self.config
        harness = self.harness
        harness.disable_hooks()
        harness.update_config(config)
        harness.charm.on.content_cache_pebble_ready.emit(mock.Mock())
        self.assertEqual(
            harness.charm.unit.status, MaintenanceStatus('Configuring workload container (config-changed)')
        )
        configure_workload_container.assert_called_once()

    def test_on_start(self):
        """Test on_start, nothing but setting ActiveStatus."""
        harness = self.harness
        harness.charm.on.start.emit()
        self.assertEqual(harness.charm.unit.status, ActiveStatus('Started'))

    @mock.patch('charm.ContentCacheCharm.configure_workload_container')
    def test_on_config_changed(self, configure_workload_container):
        """Test on_config_changed, ensure configure_workload_container is called just once."""
        config = self.config
        harness = self.harness
        harness.update_config(config)
        self.assertEqual(
            harness.charm.unit.status, MaintenanceStatus('Configuring workload container (config-changed)')
        )
        configure_workload_container.assert_called_once()

    @mock.patch('charm.ContentCacheCharm.configure_workload_container')
    def test_on_upgrade_charm(self, configure_workload_container):
        """Test on_upgrade_charm, ensure configure_workload_container is called just once."""
        harness = self.harness
        harness.charm.on.upgrade_charm.emit()
        self.assertEqual(harness.charm.unit.status, MaintenanceStatus('Configuring workload container (upgrade-charm)'))
        configure_workload_container.assert_called_once()

    @mock.patch('charm.ContentCacheCharm._make_nginx_config')
    @mock.patch('charm.ContentCacheCharm._make_pebble_config')
    @mock.patch('charms.nginx_ingress_integrator.v0.ingress.IngressRequires.update_config')
    @mock.patch('ops.model.Container.add_layer')
    @mock.patch('ops.model.Container.get_service')
    @mock.patch('ops.model.Container.make_dir')
    @mock.patch('ops.model.Container.push')
    @mock.patch('ops.model.Container.start')
    @mock.patch('ops.model.Container.stop')
    def test_configure_workload_container(
        self, stop, start, push, make_dir, get_service, add_layer, ingress_update, make_pebble_config, make_nginx_config
    ):
        """Test configure_workload_container and associated configuration."""
        config = self.config
        harness = self.harness
        harness.update_config(config)
        expect = {'service-hostname': 'mysite.local', 'service-name': 'content-cache-k8s', 'service-port': 80}
        ingress_update.assert_called_with(expect)
        make_pebble_config.assert_called_once()
        make_nginx_config.assert_called_once()
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
    def test_configure_workload_container_container_not_running(
        self, stop, start, push, make_dir, get_service, add_layer, make_pebble_config
    ):
        """Test configure_workload_container and associated configuration."""
        config = self.config
        harness = self.harness
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
    def test_configure_workload_container_pebble_services_already_configured(
        self, stop, start, push, make_dir, get_service, add_layer, make_pebble_config
    ):
        """Test configure_workload_container and associated configuration."""
        config = self.config
        harness = self.harness

        return
        # harness.charm._stored.content_cache_pebble_ready = True
        config = copy.deepcopy(BASE_CONFIG)
        make_pebble_config.return_value = {'services': {}}
        harness.update_config(config)
        make_pebble_config.assert_called_once()
        add_layer.assert_not_called()
        self.assertEqual(harness.charm.unit.status, ActiveStatus('Ready'))

    @mock.patch('charm.ContentCacheCharm._make_pebble_config')
    def test_configure_workload_container_missing_configs(self, make_pebble_config):
        """Test configure_workload_container and associated configuration."""
        config = self.config
        harness = self.harness
        config['site'] = None
        harness.update_config(config)
        make_pebble_config.assert_not_called()
        self.assertEqual(harness.charm.unit.status, BlockedStatus('Required config(s) empty: site'))

    def test_generate_keys_zone(self):
        """Test generating hashed name for Nginx's cache key zone."""
        harness = self.harness
        harness.disable_hooks()
        expected = '39c631ffb52d-cache'
        self.assertEqual(harness.charm._generate_keys_zone('mysite.local'), expected)
        expected = '8b79f9e4b3e8-cache'
        self.assertEqual(harness.charm._generate_keys_zone('my-really-really-really-long-site-name.local'), expected)
        expected = 'd41d8cd98f00-cache'
        self.assertEqual(harness.charm._generate_keys_zone(''), expected)

    def test_make_ingress_config(self):
        """Test generation ingress config and ensure it is correct."""
        config = self.config
        harness = self.harness
        harness.disable_hooks()
        harness.update_config(config)
        expected = copy.deepcopy(INGRESS_CONFIG)
        self.assertEqual(harness.charm._make_ingress_config(), expected)

    def test_make_ingress_config_client_max_body_size(self):
        """Test generation ingress config overriding client_max_body_size and ensure it is correct."""
        config = self.config
        harness = self.harness
        harness.disable_hooks()
        config['client_max_body_size'] = '50m'
        harness.update_config(config)
        expected = copy.deepcopy(INGRESS_CONFIG)
        expected['max-body-size'] = '50m'
        self.assertEqual(harness.charm._make_ingress_config(), expected)

    def test_make_ingress_config_tls_secret(self):
        """Test generation ingress config setting tls_secret_name and ensure it is correct."""
        config = self.config
        harness = self.harness
        harness.disable_hooks()
        config['tls_secret_name'] = 'mysite-com-tls'
        harness.update_config(config, unset=['client_max_body_size'])
        expected = copy.deepcopy(INGRESS_CONFIG)
        expected['tls-secret-name'] = 'mysite-com-tls'
        self.assertEqual(harness.charm._make_ingress_config(), expected)

    def test_make_env_config(self):
        """Test make_env_config, ensure correct."""
        config = self.config
        harness = self.harness
        harness.disable_hooks()
        harness.update_config(config)
        expected = JUJU_ENV_CONFIG
        expected['CONTENT_CACHE_BACKEND'] = 'http://mybackend.local:80'
        expected['CONTENT_CACHE_SITE'] = 'mysite.local'
        self.assertEqual(harness.charm._make_env_config(), expected)

    def test_make_pebble_config(self):
        """Test make_pebble_config, ensure correct."""
        config = self.config
        harness = self.harness
        harness.disable_hooks()
        harness.update_config(config)
        env_config = harness.charm._make_env_config()
        expected = PEBBLE_CONFIG
        expected['services']['content-cache']['environment'] = harness.charm._make_env_config()
        self.assertEqual(harness.charm._make_pebble_config(env_config), expected)

    def test_make_nginx_config(self):
        """Test make_nginx_config, ensure envConfig returned is correct."""
        config = self.config
        harness = self.harness
        harness.disable_hooks()
        harness.update_config(config)
        env_config = harness.charm._make_env_config()
        with open('tests/files/nginx_config.txt', 'r') as f:
            expected = f.read()
            self.assertEqual(harness.charm._make_nginx_config(env_config), expected)

    def test_make_nginx_config_backend_site_name(self):
        """Test make_nginx_config with charm config backend_site_config, ensure envConfig returned is correct."""
        config = self.config
        harness = self.harness
        harness.disable_hooks()
        config['backend_site_name'] = 'myoverridebackendsitename.local'
        harness.update_config(config)
        env_config = harness.charm._make_env_config()
        with open('tests/files/nginx_config_backend_site_name.txt', 'r') as f:
            expected = f.read()
            self.assertEqual(harness.charm._make_nginx_config(env_config), expected)

    def test_make_nginx_config_client_max_body_size(self):
        """Test make_nginx_config with charm config client_max_body_size, ensure returned is correct."""
        config = self.config
        harness = self.harness
        harness.disable_hooks()
        config['client_max_body_size'] = '50m'
        harness.update_config(config)
        env_config = harness.charm._make_env_config()
        with open('tests/files/nginx_config_client_max_body_size.txt', 'r') as f:
            expected = f.read()
            self.assertEqual(harness.charm._make_nginx_config(env_config), expected)

    def test_missing_charm_configs(self):
        """Test missing_charm_config, ensure required configs present and return those missing."""
        config = self.config
        harness = self.harness
        harness.disable_hooks()
        # None missing, all required configs set.
        harness.update_config(config)
        expected = []
        self.assertEqual(harness.charm._missing_charm_configs(), expected)

    def test_missing_charm_configs_missing_all(self):
        """Test missing_charm_config, ensure required configs present and return those missing."""
        config = self.config
        harness = self.harness
        harness.disable_hooks()
        # All missing, should be sorted.
        config.pop('backend')
        config.pop('site')
        harness.update_config(config)
        expected = ['backend', 'site']
        self.assertEqual(harness.charm._missing_charm_configs(), expected)

    def test_missing_charm_configs_missing_one(self):
        """Test missing_charm_config, ensure required configs present and return those missing."""
        config = self.config
        harness = self.harness
        harness.disable_hooks()
        # One missing.
        config.pop('site')
        harness.update_config(config)
        expected = ['site']
        self.assertEqual(harness.charm._missing_charm_configs(), expected)

    def test_missing_charm_configs_unset_all(self):
        """Test missing_charm_config, ensure required configs present and return those missing."""
        config = self.config
        harness = self.harness
        harness.disable_hooks()
        # All set to None, should be sorted.
        config['backend'] = None
        config['site'] = None
        harness.update_config(config)
        expected = ['backend', 'site']
        self.assertEqual(harness.charm._missing_charm_configs(), expected)

    def test_missing_charm_configs_unset_one(self):
        """Test missing_charm_config, ensure required configs present and return those missing."""
        config = self.config
        harness = self.harness
        harness.disable_hooks()
        # One set to None
        config['site'] = None
        harness.update_config(config)
        expected = ['site']
        self.assertEqual(harness.charm._missing_charm_configs(), expected)
