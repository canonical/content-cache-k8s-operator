# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

import copy
import unittest
from unittest import mock

from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus, WaitingStatus
from ops.testing import Harness

from charm import ContentCacheCharm

BASE_CONFIG = {
    "site": "mysite.local",
    "backend": "http://mybackend.local:80",
    "cache_max_size": "10G",
    "cache_use_stale": "error timeout updating http_500 http_502 http_503 http_504",
    "cache_valid": "200 1h",
}
CACHE_PATH = "/var/lib/nginx/proxy/cache"
CONTAINER_NAME = "content-cache"
CONTAINER_PORT = 80
JUJU_ENV_CONFIG = {
    "JUJU_POD_NAME": "content-cache-k8s/0",
    "JUJU_POD_NAMESPACE": None,
    "JUJU_POD_SERVICE_ACCOUNT": "content-cache-k8s",
    "NGINX_BACKEND_SITE_NAME": "mybackend.local",
    "NGINX_CACHE_ALL": False,
    "NGINX_CACHE_INACTIVE_TIME": "10m",
    "NGINX_CACHE_MAX_SIZE": "10G",
    "NGINX_CACHE_PATH": "/var/lib/nginx/proxy/cache",
    "NGINX_CACHE_USE_STALE": "error timeout updating http_500 http_502 http_503 http_504",
    "NGINX_CACHE_VALID": "200 1h",
    "NGINX_CLIENT_MAX_BODY_SIZE": "1m",
}
INGRESS_CONFIG = {
    "max-body-size": "1m",
    "service-hostname": "mysite.local",
    "service-name": "content-cache-k8s",
    "service-port": CONTAINER_PORT,
}
PEBBLE_CONFIG = {
    "summary": "content-cache layer",
    "description": "Pebble config layer for content-cache",
    "services": {
        CONTAINER_NAME: {
            "override": "replace",
            "summary": "content-cache",
            "command": "/usr/sbin/nginx -g 'daemon off;'",
            "startup": "false",
            "environment": "",
        },
    },
}


class TestCharm(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

        self.config = copy.deepcopy(BASE_CONFIG)
        self.harness = Harness(ContentCacheCharm)
        self.harness.begin()

    def tearDown(self):
        # starting from ops 0.8, we also need to do:
        self.addCleanup(self.harness.cleanup)

    @mock.patch("charm.ContentCacheCharm.configure_workload_container")
    def test_on_content_cache_pebble_ready(self, configure_workload_container):
        """
        arrange: content_cache_pebble_ready event is received
        act: configure workload container
        assert: workload is called just once
        """
        config = self.config
        harness = self.harness
        harness.disable_hooks()
        harness.update_config(config)
        harness.charm.on.content_cache_pebble_ready.emit(mock.Mock())
        self.assertEqual(
            harness.charm.unit.status,
            MaintenanceStatus("Configuring workload container (config-changed)"),
        )
        configure_workload_container.assert_called_once()

    def test_on_start(self):
        """
        arrange: workload container started
        act: change unit status
        assert: unit status is Started
        """
        harness = self.harness
        harness.charm.on.start.emit()
        self.assertEqual(harness.charm.unit.status, ActiveStatus("Started"))

    @mock.patch("charm.ContentCacheCharm.configure_workload_container")
    def test_on_config_changed(self, configure_workload_container):
        """
        arrange: config is changed
        act: update config
        assert: workload is called just once
        """
        config = self.config
        harness = self.harness
        harness.update_config(config)
        self.assertEqual(
            harness.charm.unit.status,
            MaintenanceStatus("Configuring workload container (config-changed)"),
        )
        configure_workload_container.assert_called_once()

    @mock.patch("charm.ContentCacheCharm.configure_workload_container")
    def test_on_upgrade_charm(self, configure_workload_container):
        """
        arrange: charm is upgraded
        act: configure workload container
        assert: workload is called just once
        """
        harness = self.harness
        harness.charm.on.upgrade_charm.emit()
        self.assertEqual(
            harness.charm.unit.status,
            MaintenanceStatus("Configuring workload container (upgrade-charm)"),
        )
        configure_workload_container.assert_called_once()

    @mock.patch("charm.ContentCacheCharm._make_nginx_config")
    @mock.patch("charm.ContentCacheCharm._make_pebble_config")
    @mock.patch("charms.nginx_ingress_integrator.v0.ingress.IngressRequires.update_config")
    @mock.patch("ops.model.Container.add_layer")
    @mock.patch("ops.model.Container.get_service")
    @mock.patch("ops.model.Container.make_dir")
    @mock.patch("ops.model.Container.push")
    @mock.patch("ops.model.Container.start")
    @mock.patch("ops.model.Container.stop")
    def test_configure_workload_container(
        self,
        stop,
        start,
        push,
        make_dir,
        get_service,
        add_layer,
        ingress_update,
        make_pebble_config,
        make_nginx_config,
    ):
        """
        arrange: config is changed
        act: configure workload container
        assert: unit status is Ready
        """
        config = self.config
        harness = self.harness
        harness.update_config(config)
        expect = {
            "max-body-size": "1m",
            "service-hostname": "mysite.local",
            "service-name": "content-cache-k8s",
            "service-port": 80,
        }
        ingress_update.assert_called_with(expect)
        make_pebble_config.assert_called_once()
        make_nginx_config.assert_called_once()
        add_layer.assert_called_once()
        get_service.assert_called_once()
        stop.assert_called_once()
        start.assert_called_once()
        self.assertEqual(harness.charm.unit.status, ActiveStatus("Ready"))

    @mock.patch("charm.ContentCacheCharm._make_pebble_config")
    @mock.patch("ops.model.Container.add_layer")
    @mock.patch("ops.model.Container.get_service")
    @mock.patch("ops.model.Container.make_dir")
    @mock.patch("ops.model.Container.push")
    @mock.patch("ops.model.Container.start")
    @mock.patch("ops.model.Container.stop")
    def test_configure_workload_container_container_not_running(
        self, stop, start, push, make_dir, get_service, add_layer, make_pebble_config
    ):
        """
        arrange: config is changed
        act: check if service is running and is not
        assert: workload container is stopped
        """
        config = self.config
        harness = self.harness
        harness.update_config(config)
        make_pebble_config.assert_called_once()
        get_service.return_value.is_running.return_value = False
        harness.update_config(config)
        stop.assert_called_once()

    @mock.patch("charm.ContentCacheCharm._make_pebble_config")
    @mock.patch("ops.model.Container.add_layer")
    @mock.patch("ops.model.Container.get_service")
    @mock.patch("ops.model.Container.make_dir")
    @mock.patch("ops.model.Container.push")
    @mock.patch("ops.model.Container.start")
    @mock.patch("ops.model.Container.stop")
    def test_configure_workload_container_pebble_services_already_configured(
        self, stop, start, push, make_dir, get_service, add_layer, make_pebble_config
    ):
        """
        arrange: config is changed
        act: check if current config is different and is not
        assert: no action
        """
        config = self.config
        harness = self.harness

        config = copy.deepcopy(BASE_CONFIG)
        make_pebble_config.return_value = {"services": {}}
        harness.update_config(config)
        make_pebble_config.assert_called_once()
        add_layer.assert_not_called()
        self.assertEqual(harness.charm.unit.status, ActiveStatus("Ready"))

    @mock.patch("charm.ContentCacheCharm._make_pebble_config")
    @mock.patch("ops.model.Container.add_layer")
    @mock.patch("ops.model.Container.get_service")
    @mock.patch("ops.model.Container.make_dir")
    @mock.patch("ops.model.Container.push")
    @mock.patch("ops.model.Container.start")
    @mock.patch("ops.model.Container.stop")
    @mock.patch("ops.model.Container.isdir")
    def test_configure_workload_container_has_cache_directory(
        self, stop, start, push, make_dir, get_service, add_layer, make_pebble_config, isdir
    ):
        """
        arrange: workload container is ready
        act: check if cache dir is created
        assert: cache directory is created
        """
        config = self.config
        harness = self.harness

        config = copy.deepcopy(BASE_CONFIG)
        harness.update_config(config)
        make_pebble_config.assert_called_once()
        self.assertEqual(harness.charm.unit.status, ActiveStatus("Ready"))
        container = harness.charm.unit.get_container(CONTAINER_NAME)
        self.assertTrue(container.isdir(CACHE_PATH))

    @mock.patch("charm.ContentCacheCharm._make_pebble_config")
    @mock.patch("ops.model.Container.add_layer")
    @mock.patch("ops.model.Container.get_service")
    @mock.patch("ops.model.Container.make_dir")
    @mock.patch("ops.model.Container.push")
    @mock.patch("ops.model.Container.start")
    @mock.patch("ops.model.Container.stop")
    def test_configure_workload_container_pebble_not_ready(
        self, stop, start, push, make_dir, get_service, add_layer, make_pebble_config
    ):
        """
        arrange: config is changed
        act: raises exception
        assert: unit status is Waiting
        """
        config = self.config
        harness = self.harness

        config = copy.deepcopy(BASE_CONFIG)
        make_pebble_config.return_value = {"services": {}}
        push.side_effect = ConnectionError
        harness.update_config(config)
        self.assertEqual(
            harness.charm.unit.status,
            WaitingStatus("Pebble is not ready, deferring event"),
        )

    @mock.patch("charm.ContentCacheCharm._make_pebble_config")
    def test_configure_workload_container_missing_configs(self, make_pebble_config):
        """
        arrange: config is empty
        act: raises exception
        assert: unit status is Blocked
        """
        config = self.config
        harness = self.harness
        config["site"] = None
        harness.update_config(config)
        make_pebble_config.assert_not_called()
        self.assertEqual(
            harness.charm.unit.status, BlockedStatus("Required config(s) empty: site")
        )

    def test_generate_keys_zone(self):
        """
        arrange: set value for env variable NGINX_KEYS_ZONE
        act: generate keys zone
        assert: keys zone is generated as expected
        """
        harness = self.harness
        harness.disable_hooks()
        expected = "39c631ffb52d-cache"
        self.assertEqual(harness.charm._generate_keys_zone("mysite.local"), expected)
        expected = "8b79f9e4b3e8-cache"
        self.assertEqual(
            harness.charm._generate_keys_zone("my-really-really-really-long-site-name.local"),
            expected,
        )
        expected = "d41d8cd98f00-cache"
        self.assertEqual(harness.charm._generate_keys_zone(""), expected)

    def test_make_ingress_config(self):
        """
        arrange: set ingress config
        act: generate ingress config
        assert: ingress config is generated as expected
        """
        config = self.config
        harness = self.harness
        harness.disable_hooks()
        harness.update_config(config)
        expected = copy.deepcopy(INGRESS_CONFIG)
        self.assertEqual(harness.charm._make_ingress_config(), expected)

    def test_make_ingress_config_client_max_body_size(self):
        """
        arrange: set ingress config overriding client_max_body_size
        act: generate ingress config
        assert: client_max_body_size is overridden as expected
        """
        config = self.config
        harness = self.harness
        harness.disable_hooks()
        config["client_max_body_size"] = "50m"
        harness.update_config(config)
        expected = copy.deepcopy(INGRESS_CONFIG)
        expected["max-body-size"] = "50m"
        self.assertEqual(harness.charm._make_ingress_config(), expected)

    def test_make_ingress_config_tls_secret(self):
        """
        arrange: set tls_secret_name ingress config
        act: generate tls_secret_name ingress config
        assert: tls_secret_name is correct
        """
        config = self.config
        harness = self.harness
        harness.disable_hooks()
        config["tls_secret_name"] = "mysite-com-tls"
        harness.update_config(config)
        expected = copy.deepcopy(INGRESS_CONFIG)
        expected["tls-secret-name"] = "mysite-com-tls"
        self.assertEqual(harness.charm._make_ingress_config(), expected)

    def test_make_env_config(self):
        """
        arrange: define env variables
        act: set env variables
        assert: env variables are correct
        """
        config = self.config
        harness = self.harness
        harness.disable_hooks()
        harness.update_config(config)
        expected = JUJU_ENV_CONFIG
        expected["CONTAINER_PORT"] = 80
        expected["CONTENT_CACHE_BACKEND"] = "http://mybackend.local:80"
        expected["CONTENT_CACHE_SITE"] = "mysite.local"
        expected["NGINX_BACKEND"] = "http://mybackend.local:80"
        expected["NGINX_KEYS_ZONE"] = harness.charm._generate_keys_zone("mysite.local")
        expected["NGINX_SITE_NAME"] = "mysite.local"
        expected["NGINX_CACHE_ALL"] = "proxy_ignore_headers Cache-Control Expires;"
        self.assertEqual(harness.charm._make_env_config(), expected)

    def test_make_pebble_config(self):
        """
        arrange: define pebble config
        act: set pebble config
        assert: pebble config is correct
        """
        config = self.config
        harness = self.harness
        harness.disable_hooks()
        harness.update_config(config)
        env_config = harness.charm._make_env_config()
        expected = PEBBLE_CONFIG
        expected["services"]["content-cache"]["environment"] = harness.charm._make_env_config()
        self.assertEqual(harness.charm._make_pebble_config(env_config), expected)

    def test_make_nginx_config(self):
        """
        arrange: define nginx config
        act: set nginx config
        assert: ensure envConfig returned is correct
        """
        config = self.config
        harness = self.harness
        harness.disable_hooks()
        harness.update_config(config)
        env_config = harness.charm._make_env_config()
        with open("tests/files/nginx_config.txt", "r") as f:
            expected = f.read()
            self.assertEqual(harness.charm._make_nginx_config(env_config), expected)

    def test_make_nginx_config_backend_site_name(self):
        """
        arrange: define nginx config with charm config backend_site_config
        act: set nginx config
        assert: ensure envConfig returned is correct
        """
        config = self.config
        harness = self.harness
        harness.disable_hooks()
        config["backend_site_name"] = "myoverridebackendsitename.local"
        harness.update_config(config)
        env_config = harness.charm._make_env_config()
        with open("tests/files/nginx_config_backend_site_name.txt", "r") as f:
            expected = f.read()
            self.assertEqual(harness.charm._make_nginx_config(env_config), expected)

    def test_make_nginx_config_client_max_body_size(self):
        """
        arrange: define nginx config with charm config client_max_body_size
        act: set nginx config
        assert: ensure envConfig returned is correct
        """
        config = self.config
        harness = self.harness
        harness.disable_hooks()
        config["client_max_body_size"] = "50m"
        harness.update_config(config)
        env_config = harness.charm._make_env_config()
        with open("tests/files/nginx_config_client_max_body_size.txt", "r") as f:
            expected = f.read()
            self.assertEqual(harness.charm._make_nginx_config(env_config), expected)

    def test_missing_charm_configs(self):
        """
        arrange: define charm config with missing field
        act: set charm config
        assert: ensure required configs present and return those missing
        """
        config = self.config
        harness = self.harness
        harness.disable_hooks()
        # None missing, all required configs set.
        harness.update_config(config)
        expected = []
        self.assertEqual(harness.charm._missing_charm_configs(), expected)

    def test_missing_charm_configs_missing_all(self):
        """
        arrange: define charm config with all missing
        act: set charm config
        assert: ensure required configs present and return those missing
        """
        config = self.config
        harness = self.harness
        harness.disable_hooks()
        # All missing, should be sorted.
        config.pop("backend")
        config.pop("site")
        harness.update_config(config)
        expected = ["backend", "site"]
        self.assertEqual(harness.charm._missing_charm_configs(), expected)

    def test_missing_charm_configs_missing_one(self):
        """
        arrange: define charm config with missing one
        act: set charm config
        assert: ensure required configs present and return those missing
        """
        config = self.config
        harness = self.harness
        harness.disable_hooks()
        # One missing.
        config.pop("site")
        harness.update_config(config)
        expected = ["site"]
        self.assertEqual(harness.charm._missing_charm_configs(), expected)

    def test_missing_charm_configs_unset_all(self):
        """
        arrange: define charm config with all unset
        act: set charm config
        assert: ensure required configs present and return those missing
        """
        config = self.config
        harness = self.harness
        harness.disable_hooks()
        # All set to None, should be sorted.
        config["backend"] = None
        config["site"] = None
        harness.update_config(config)
        expected = ["backend", "site"]
        self.assertEqual(harness.charm._missing_charm_configs(), expected)

    def test_missing_charm_configs_unset_one(self):
        """
        arrange: define charm config with one unset
        act: set charm config
        assert: ensure required configs present and return those missing
        """
        config = self.config
        harness = self.harness
        harness.disable_hooks()
        # One set to None
        config["site"] = None
        harness.update_config(config)
        expected = ["site"]
        self.assertEqual(harness.charm._missing_charm_configs(), expected)
