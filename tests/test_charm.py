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
POD_SPEC_TMPL = {
    'version': 3,
    'containers': [
        {
            'name': 'content-cache',
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
K8S_RESOURCES_TMPL = {
    'kubernetesResources': {
        'ingressResources': [
            {
                'annotations': {'nginx.ingress.kubernetes.io/ssl-redirect': 'false'},
                'name': 'content-cache-ingress',
                'spec': {
                    'rules': [
                        {
                            'host': 'mysite.local',
                            'http': {
                                'paths': [
                                    {
                                        'backend': {'serviceName': 'content-cache', 'servicePort': 80},
                                        'path': '/',
                                    }
                                ]
                            },
                        }
                    ]
                },
            }
        ]
    }
}


class TestCharm(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.harness = Harness(ContentCacheCharm)

    def tearDown(self):
        # starting from ops 0.8, we also need to do:
        self.addCleanup(self.harness.cleanup)

    def test_on_start(self):
        harness = self.harness
        action_event = mock.Mock()

        harness.begin()
        harness.charm._on_start(action_event)
        self.assertEqual(harness.charm.unit.status, ActiveStatus('Started'))

    @mock.patch('charm.ContentCacheCharm.configure_pod')
    def test_on_config_changed(self, configure_pod):
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
        harness = self.harness

        harness.begin()
        # Intentionally after harness.begin() to trigger leadership events.
        harness.set_leader(True)
        self.assertEqual(harness.charm.unit.status, MaintenanceStatus('Configuring pod (leader-elected)'))
        configure_pod.assert_called_once()

    @mock.patch('charm.ContentCacheCharm.configure_pod')
    def test_on_leader_elected_not_leader(self, configure_pod):
        harness = self.harness

        harness.begin()
        # Intentionally after harness.begin() to trigger leadership events.
        harness.set_leader(False)
        self.assertNotEqual(harness.charm.unit.status, MaintenanceStatus('Configuring pod (leader-elected)'))
        configure_pod.assert_not_called()

    @mock.patch('charm.ContentCacheCharm.configure_pod')
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

    @mock.patch('charm.ContentCacheCharm.configure_pod')
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

    @mock.patch('charm.ContentCacheCharm._make_pod_spec')
    def test_configure_pod(self, make_pod_spec):
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
        harness = self.harness

        harness.disable_hooks()
        harness.begin()

        config = copy.deepcopy(BASE_CONFIG)
        harness.update_config(config)
        k8s_resources = copy.deepcopy(K8S_RESOURCES_TMPL)
        expected = k8s_resources['kubernetesResources']['ingressResources']
        self.assertEqual(harness.charm._make_k8s_ingress_spec(), expected)

    def test_make_k8s_ingress_spec_client_max_body_size(self):
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
        harness = self.harness

        harness.disable_hooks()
        harness.begin()

        config = copy.deepcopy(BASE_CONFIG)
        harness.update_config(config)
        expected = {
            'NGINX_BACKEND': 'http://mybackend.local:80',
            'NGINX_CACHE_INACTIVE_TIME': '10m',
            'NGINX_CACHE_MAX_SIZE': '10G',
            'NGINX_CACHE_PATH': CACHE_PATH,
            'NGINX_CACHE_USE_STALE': 'error timeout updating http_500 http_502 http_503 http_504',
            'NGINX_CACHE_VALID': '200 1h',
            'NGINX_CLIENT_MAX_BODY_SIZE': '1m',
            'NGINX_KEYS_ZONE': '39c631ffb52d-cache',
            'NGINX_SITE_NAME': 'mysite.local',
        }
        self.assertEqual(harness.charm._make_pod_config(), expected)

    def test_make_pod_config_client_max_body_size(self):
        harness = self.harness

        harness.disable_hooks()
        harness.begin()

        config = copy.deepcopy(BASE_CONFIG)
        config['client_max_body_size'] = '50m'
        harness.update_config(config)
        expected = {
            'NGINX_BACKEND': 'http://mybackend.local:80',
            'NGINX_CACHE_INACTIVE_TIME': '10m',
            'NGINX_CACHE_MAX_SIZE': '10G',
            'NGINX_CACHE_PATH': CACHE_PATH,
            'NGINX_CACHE_USE_STALE': 'error timeout updating http_500 http_502 http_503 http_504',
            'NGINX_CACHE_VALID': '200 1h',
            'NGINX_CLIENT_MAX_BODY_SIZE': '50m',
            'NGINX_KEYS_ZONE': '39c631ffb52d-cache',
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
