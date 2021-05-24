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
    'image_path': 'localhost:32000/myimage:latest',
    'site': 'mysite.local',
    'backend': 'http://mybackend.local:80',
    'cache_max_size': '10G',
    'cache_use_stale': 'error timeout updating http_500 http_502 http_503 http_504',
    'cache_valid': '200 1h',
}
CACHE_PATH = '/var/lib/nginx/proxy/cache'
CONTAINER_PORT = 80
JUJU_ENV_CONFIG = {
    'JUJU_NODE_NAME': {'field': {'api-version': 'v1', 'path': 'spec.nodeName'}},
    'JUJU_POD_NAME': {'field': {'api-version': 'v1', 'path': 'metadata.name'}},
    'JUJU_POD_NAMESPACE': {'field': {'api-version': 'v1', 'path': 'metadata.namespace'}},
    'JUJU_POD_IP': {'field': {'api-version': 'v1', 'path': 'status.podIP'}},
    'JUJU_POD_SERVICE_ACCOUNT': {'field': {'api-version': 'v1', 'path': 'spec.serviceAccountName'}},
}
K8S_RESOURCES_INGRESS_RULES = {
    'host': 'mysite.local',
    'http': {
        'paths': [
            {
                'backend': {'serviceName': 'content-cache-k8s', 'servicePort': 80},
                'path': '/',
            }
        ]
    },
}
K8S_RESOURCES_TMPL = {
    'kubernetesResources': {
        'ingressResources': [
            {
                'annotations': {'nginx.ingress.kubernetes.io/ssl-redirect': 'false'},
                'name': 'content-cache-k8s-ingress',
                'spec': {
                    'rules': [K8S_RESOURCES_INGRESS_RULES],
                },
            }
        ]
    }
}
POD_SPEC_TMPL = {
    'version': 3,
    'containers': [
        {
            'name': 'content-cache-k8s',
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
    ],
}


class TestCharm(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.harness = Harness(ContentCacheCharm)

    def tearDown(self):
        # starting from ops 0.8, we also need to do:
        self.addCleanup(self.harness.cleanup)

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

        # Intentionally before harness.begin() to avoid firing leadership events.
        harness.set_leader(True)
        harness.begin()

        config = copy.deepcopy(BASE_CONFIG)
        harness.update_config(config)
        self.assertEqual(harness.charm.unit.status, MaintenanceStatus('Configuring pod (config-changed)'))
        configure_pod.assert_called_once()

    @mock.patch('charm.ContentCacheCharm.configure_pod')
    def test_on_config_changed_not_leader(self, configure_pod):
        """Test on_config_chaned, not the leader so configure_pod not called."""
        harness = self.harness

        # Intentionally before harness.begin() to avoid firing leadership events.
        harness.set_leader(False)
        harness.begin()

        config = copy.deepcopy(BASE_CONFIG)
        harness.update_config(config)
        self.assertNotEqual(harness.charm.unit.status, MaintenanceStatus('Configuring pod (config-changed)'))
        configure_pod.assert_not_called()

    @mock.patch('charm.ContentCacheCharm.configure_pod')
    def test_on_leader_elected(self, configure_pod):
        """Test on_leader_elected, ensure configure_pod is called just once."""
        harness = self.harness

        harness.begin()
        # Intentionally after harness.begin() to trigger leadership events.
        harness.set_leader(True)
        self.assertEqual(harness.charm.unit.status, MaintenanceStatus('Configuring pod (leader-elected)'))
        configure_pod.assert_called_once()

    @mock.patch('charm.ContentCacheCharm.configure_pod')
    def test_on_leader_elected_not_leader(self, configure_pod):
        """Test on_leader_elected, not the leader so configure_pod is not called."""
        harness = self.harness

        harness.begin()
        # Intentionally after harness.begin() to trigger leadership events.
        harness.set_leader(False)
        self.assertNotEqual(harness.charm.unit.status, MaintenanceStatus('Configuring pod (leader-elected)'))
        configure_pod.assert_not_called()

    @mock.patch('charm.ContentCacheCharm.configure_pod')
    def test_on_upgrade_charm(self, configure_pod):
        """Test on_upgrade_charm, ensure configure_pod is called just once."""
        harness = self.harness

        harness.set_leader(True)
        harness.begin()
        harness.charm.on.upgrade_charm.emit()
        self.assertEqual(harness.charm.unit.status, MaintenanceStatus('Configuring pod (upgrade-charm)'))
        configure_pod.assert_called_once()

    @mock.patch('charm.ContentCacheCharm.configure_pod')
    def test_on_upgrade_charm_not_leader(self, configure_pod):
        """Test on_upgrade_charm, not the leader so configure_pod is not called."""
        harness = self.harness

        harness.set_leader(False)
        harness.begin()
        harness.charm.on.upgrade_charm.emit()
        self.assertNotEqual(harness.charm.unit.status, MaintenanceStatus('Configuring pod (upgrade-charm)'))
        configure_pod.assert_not_called()

    @mock.patch('charm.ContentCacheCharm._make_pod_spec')
    def test_configure_pod(self, make_pod_spec):
        """Test configure_pod, ensure make_pod_spec is called and the generated pod spec is correct."""
        harness = self.harness

        harness.set_leader(True)
        harness.begin()

        config = copy.deepcopy(BASE_CONFIG)
        harness.update_config(config)
        make_pod_spec.assert_called_once()
        self.assertEqual(harness.charm.unit.status, ActiveStatus('Ready'))
        pod_spec = harness.charm._make_pod_spec()
        k8s_resources = copy.deepcopy(K8S_RESOURCES_TMPL)
        self.assertEqual(harness.get_pod_spec(), (pod_spec, k8s_resources))

    @mock.patch('charm.ContentCacheCharm._make_pod_spec')
    def test_configure_pod_missing_configs(self, make_pod_spec):
        """Test configure_pod, missing configs so ensure make_pod_spec is not called and no pod spec set."""
        harness = self.harness

        harness.set_leader(True)
        harness.begin()

        config = copy.deepcopy(BASE_CONFIG)
        config['site'] = None
        harness.update_config(config)
        make_pod_spec.assert_not_called()
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

    def test_make_k8s_ingress_spec(self):
        """Test generation of K8s ingress spec and ensure it is correct."""
        harness = self.harness

        harness.disable_hooks()
        harness.begin()

        config = copy.deepcopy(BASE_CONFIG)
        harness.update_config(config)
        k8s_resources = copy.deepcopy(K8S_RESOURCES_TMPL)
        expected = k8s_resources['kubernetesResources']['ingressResources']
        self.assertEqual(harness.charm._make_k8s_ingress_spec(), expected)

    def test_make_k8s_ingress_spec_client_max_body_size(self):
        """Test charm config's client_max_body_size with correct annotation in generated K8s ingress spec."""
        harness = self.harness

        harness.disable_hooks()
        harness.begin()

        config = copy.deepcopy(BASE_CONFIG)
        config['client_max_body_size'] = '32m'
        harness.update_config(config)
        k8s_resources = copy.deepcopy(K8S_RESOURCES_TMPL)
        t = k8s_resources['kubernetesResources']['ingressResources'][0]['annotations']
        t['nginx.ingress.kubernetes.io/proxy-body-size'] = '32m'
        expected = k8s_resources['kubernetesResources']['ingressResources']
        self.assertEqual(harness.charm._make_k8s_ingress_spec(), expected)

    def test_make_k8s_ingress_spec_tls_secrets(self):
        """Test charm config's tls_secret_name with TLS/SSL enabled in generated K8s ingress spec."""
        harness = self.harness

        harness.disable_hooks()
        harness.begin()

        config = copy.deepcopy(BASE_CONFIG)
        config['tls_secret_name'] = '{}-tls'.format(config['site'])
        harness.update_config(config)
        k8s_resources = copy.deepcopy(K8S_RESOURCES_TMPL)
        t = k8s_resources['kubernetesResources']['ingressResources'][0]
        t.pop('annotations')
        t['spec']['tls'] = [{'hosts': 'mysite.local', 'secretName': 'mysite.local-tls'}]
        expected = k8s_resources['kubernetesResources']['ingressResources']
        self.assertEqual(harness.charm._make_k8s_ingress_spec(), expected)

    def test_make_pod_spec(self):
        """Test make_pod_spec, ensure correct spec and is applied and returned by operator's get_pod_spec."""
        harness = self.harness

        harness.set_leader(True)
        harness.begin()

        config = copy.deepcopy(BASE_CONFIG)
        harness.update_config(config)
        spec = copy.deepcopy(POD_SPEC_TMPL)
        t = spec['containers'][0]
        t['envConfig'] = harness.charm._make_pod_config()
        t['imageDetails'] = {'imagePath': 'localhost:32000/myimage:latest'}
        t['volumeConfig'] = [
            {'name': 'cache-volume', 'mountPath': '/var/lib/nginx/proxy/cache', 'emptyDir': {'sizeLimit': '10G'}}
        ]
        k8s_resources = copy.deepcopy(K8S_RESOURCES_TMPL)
        expected = (spec, k8s_resources)
        self.assertEqual(harness.get_pod_spec(), expected)

    def test_make_pod_spec_image_username(self):
        """Test charm config image_username/image_password, ensure correct pod spec with details to pod image."""
        harness = self.harness

        harness.set_leader(True)
        harness.begin()

        config = copy.deepcopy(BASE_CONFIG)
        config['image_username'] = 'myuser'
        config['image_password'] = 'mypassword'
        harness.update_config(config)
        spec = copy.deepcopy(POD_SPEC_TMPL)
        t = spec['containers'][0]
        t['envConfig'] = harness.charm._make_pod_config()
        t['imageDetails'] = {
            'imagePath': 'localhost:32000/myimage:latest',
            'username': 'myuser',
            'password': 'mypassword',
        }
        t['volumeConfig'] = [
            {'name': 'cache-volume', 'mountPath': '/var/lib/nginx/proxy/cache', 'emptyDir': {'sizeLimit': '10G'}}
        ]
        k8s_resources = copy.deepcopy(K8S_RESOURCES_TMPL)
        expected = (spec, k8s_resources)
        self.assertEqual(harness.get_pod_spec(), expected)

    def test_make_pod_spec_cache_max_size(self):
        """Test charm config's cache_max_size, ensure correct pod spec utilising volumeConfig with size limit."""
        harness = self.harness

        harness.set_leader(True)
        harness.begin()

        config = copy.deepcopy(BASE_CONFIG)
        config['cache_max_size'] = '201G'
        harness.update_config(config)
        spec = copy.deepcopy(POD_SPEC_TMPL)
        t = spec['containers'][0]
        t['envConfig'] = harness.charm._make_pod_config()
        t['imageDetails'] = {'imagePath': 'localhost:32000/myimage:latest'}
        t['volumeConfig'] = [
            {'name': 'cache-volume', 'mountPath': '/var/lib/nginx/proxy/cache', 'emptyDir': {'sizeLimit': '201G'}}
        ]
        k8s_resources = copy.deepcopy(K8S_RESOURCES_TMPL)
        expected = (spec, k8s_resources)
        self.assertEqual(harness.get_pod_spec(), expected)

    def test_make_pod_config(self):
        """Test make_pod_config, ensure envConfig returned is correct."""
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
        self.assertEqual(harness.charm._make_pod_config(), expected)

    def test_make_pod_config_backend_site_name(self):
        """Test make_pod_config with charm config backend_site_config, ensure envConfig returned is correct."""
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
        self.assertEqual(harness.charm._make_pod_config(), expected)

    def test_make_pod_config_client_max_body_size(self):
        """Test make_pod_config with charm config client_max_body_size, ensure envConfig returned is correct."""
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
        self.assertEqual(harness.charm._make_pod_config(), expected)

    def test_missing_charm_configs(self):
        """Test missing_charm_config, ensure required configs present and return those missing."""
        harness = self.harness

        harness.disable_hooks()
        harness.begin()

        # None missing.
        config = copy.deepcopy(BASE_CONFIG)
        harness.update_config(config)
        expected = []
        self.assertEqual(harness.charm._missing_charm_configs(), expected)

        # One missing.
        config = copy.deepcopy(BASE_CONFIG)
        config['site'] = None
        harness.update_config(config)
        expected = ['site']
        self.assertEqual(harness.charm._missing_charm_configs(), expected)

        # More than one missing.
        config = copy.deepcopy(BASE_CONFIG)
        config['image_path'] = None
        config['site'] = None
        harness.update_config(config)
        expected = ['image_path', 'site']
        self.assertEqual(harness.charm._missing_charm_configs(), expected)

        # All missing, should be sorted.
        config = copy.deepcopy(BASE_CONFIG)
        config['image_path'] = None
        config['image_username'] = 'myuser'
        config['backend'] = None
        config['site'] = None
        harness.update_config(config)
        expected = ['backend', 'image_password', 'image_path', 'site']
        self.assertEqual(harness.charm._missing_charm_configs(), expected)

        # image_password missing when image_username present.
        config = copy.deepcopy(BASE_CONFIG)
        config['image_username'] = 'myuser'
        harness.update_config(config)
        expected = ['image_password']
        self.assertEqual(harness.charm._missing_charm_configs(), expected)
