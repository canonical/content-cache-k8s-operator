#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Charm for Content-cache on Kubernetes."""
import hashlib
import itertools
import logging
import re
from collections import Counter
from datetime import datetime, timedelta
from urllib.parse import urlparse

import ops.pebble
from charms.grafana_k8s.v0.grafana_dashboard import GrafanaDashboardProvider
from charms.loki_k8s.v0.loki_push_api import LogProxyConsumer
from charms.nginx_ingress_integrator.v0.nginx_route import (
    _NginxRouteCharmEvents,
    provide_nginx_route,
    require_nginx_route,
)
from charms.prometheus_k8s.v0.prometheus_scrape import MetricsEndpointProvider
from ops.charm import ActionEvent, CharmBase, ConfigChangedEvent, UpgradeCharmEvent
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus, WaitingStatus
from tabulate import tabulate

from file_reader import readlines_reverse

logger = logging.getLogger(__name__)

CACHE_PATH = "/var/lib/nginx/proxy/cache"
CONTAINER_NAME = "content-cache"
EXPORTER_CONTAINER_NAME = "nginx-prometheus-exporter"
CONTAINER_PORT = 8080
REQUIRED_JUJU_CONFIGS = ["backend"]
REQUIRED_INGRESS_RELATION_FIELDS = {"service-hostname", "service-name", "service-port"}


def validate_nginx_time(value: str, config_name: str) -> None:
    """Validate nginx time format.

    Args:
        value: The time value to validate (e.g., "5s", "10m", "1h").
        config_name: The name of the configuration option for error messages.

    Raises:
        ValueError: If the time format is invalid.
    """
    # Nginx time format: <number><unit> where unit is ms, s, m, h, d, w, M, y
    # Can also be just a number (seconds) or have multiple parts like "1h 30m"
    pattern = r"^(\d+(\.\d+)?(ms|[smhdwMy])?(\s+)?)+$"
    if not re.match(pattern, value.strip()):
        raise ValueError(
            f"Invalid time format for {config_name}: '{value}'. "
            "Expected format: <number>[ms|s|m|h|d|w|M|y] (e.g., '5s', '10m', '1h')"
        )


class ContentCacheCharm(CharmBase):
    """Charm the service.

    Attrs:
        on: Ingress Charm Events
        ERROR_LOG_PATH: NGINX error log
        ACCESS_LOG_PATH: NGINX access log
        _metrics_endpoint: Provider of metrics for Prometheus charm
        _logging: Requirer of logs for Loki charm
        _grafana_dashboards: Dashboard Provider for Grafana charm
        unit: Charm's designated juju unit
        model: Charm's designated juju model
    """

    on = _NginxRouteCharmEvents()
    ERROR_LOG_PATH = "/var/log/nginx/error.log"
    ACCESS_LOG_PATH = "/var/log/nginx/access.log"

    def __init__(self, *args):
        """Init function for the charm.

        Args:
            args: Variable list of positional arguments passed to the parent constructor.
        """
        super().__init__(*args)

        self.framework.observe(self.on.start, self._on_start)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.upgrade_charm, self._on_upgrade_charm)
        self.framework.observe(
            self.on.report_visits_by_ip_action, self._report_visits_by_ip_action
        )
        self.framework.observe(
            self.on.content_cache_pebble_ready, self._on_content_cache_pebble_ready
        )
        # Provide ability for Content-cache to be scraped by Prometheus using prometheus_scrape
        self._metrics_endpoint = MetricsEndpointProvider(
            self, jobs=[{"static_configs": [{"targets": ["*:9113"]}]}]
        )

        # Enable log forwarding for Loki and other charms that implement loki_push_api
        self._logging = LogProxyConsumer(
            self,
            relation_name="logging",
            log_files=[self.ACCESS_LOG_PATH, self.ERROR_LOG_PATH],
            container_name=CONTAINER_NAME,
        )

        # Provide grafana dashboards over a relation interface
        self._grafana_dashboards = GrafanaDashboardProvider(
            self, relation_name="grafana-dashboard"
        )
        ingress_config = self._make_ingress_config()
        require_nginx_route(
            charm=self,
            max_body_size=ingress_config.get("max-body-size", None),
            service_hostname=ingress_config.get("service-hostname"),
            service_name=ingress_config.get("service-name"),
            service_port=ingress_config.get("service-port"),
            tls_secret_name=ingress_config.get("tls-secret-name", None),
        )
        provide_nginx_route(
            charm=self,
            on_nginx_route_available=self._on_config_changed,
            on_nginx_route_broken=self._on_config_changed,
            nginx_route_relation_name="nginx-proxy",
        )
        self.framework.observe(self.on.nginx_route_available, self._on_config_changed)

    def _on_content_cache_pebble_ready(self, event) -> None:
        """Handle content_cache_pebble_ready event and configure workload container.

        Args:
            event: Event triggering the pebble ready hook for the content-cache container.
        """
        msg = "Configuring workload container (content-cache-pebble-ready)"
        logger.info(msg)
        self.model.unit.status = MaintenanceStatus(msg)
        self.on.config_changed.emit()

    def _on_start(self, event) -> None:
        """Handle workload container started.

        Args:
            event: start event.
        """
        logger.info("Starting workload container (start)")
        self.model.unit.status = ActiveStatus()

    def _on_config_changed(self, event) -> None:
        """Handle config_changed event and reconfigure workload container.

        Args:
            event: config-changed event.
        """
        msg = "Configuring workload container (config-changed)"
        logger.info(msg)
        self.model.unit.status = MaintenanceStatus(msg)
        self.configure_workload_container(event)

    def _report_visits_by_ip_action(self, event: ActionEvent) -> None:
        """Handle the report-visits-by-ip action.

        Args:
            event: the Juju action event fired when the action executes.
        """
        results = self._report_visits_by_ip()
        event.set_results({"ips": tabulate(results, headers=["IP", "Requests"], tablefmt="grid")})

    @staticmethod
    def _filter_lines(line: str) -> bool:
        """Filter the log lines by date.

        Args:
            line: A log line from the log file.

        Returns:
            Indicates if the line must be included or not.
        """
        line_elements = line.split()

        if len(line_elements) < 4:
            return False

        timestamp_str = line_elements[3].lstrip("[").rstrip("]")
        try:
            timestamp = datetime.strptime(timestamp_str, "%d/%b/%Y:%H:%M:%S")
        except ValueError:
            return False

        return timestamp > (datetime.now() - timedelta(minutes=20))

    def _get_ip(self, line: str) -> str:
        """Return the IP address of a log line.

        Args:
            line: The log line previously filtered.

        Returns:
            an IP address.

        Raises:
            ValueError: if the method encounters an empty line,
                filtering should happen in filter_lines anyway.
        """
        if line:
            return line.split()[0]
        raise ValueError

    def _report_visits_by_ip(self) -> list[tuple[int, str]]:
        """Report requests to nginx grouped and ordered by IP and report action result.

        Returns:
            A list of tuples composed of an IP address and the number of visits to that IP.
        """
        container = self.unit.get_container(CONTAINER_NAME)
        reversed_lines = filter(None, readlines_reverse(container.pull(self.ACCESS_LOG_PATH)))
        line_list = itertools.takewhile(self._filter_lines, reversed_lines)
        ip_list = map(self._get_ip, line_list)

        return Counter(ip_list).most_common()

    def _on_upgrade_charm(self, event: UpgradeCharmEvent) -> None:
        """Handle upgrade_charm event and reconfigure workload container.

        Args:
            event: upgrade-charm event.
        """
        msg = "Configuring workload container (upgrade-charm)"
        logger.info(msg)
        self.model.unit.status = MaintenanceStatus(msg)
        self.configure_workload_container(event)

    def configure_workload_container(self, event: ConfigChangedEvent) -> None:
        """Configure/set up workload container inside pod.

        Args:
            event: config-changed event.
        """
        missing = sorted(self._missing_charm_configs())
        if missing:
            msg = f"Required config(s) empty: {', '.join(missing)}"
            logger.warning(msg)
            self.unit.status = BlockedStatus(msg)
            return

        try:
            env_config = self._make_env_config()
        except ValueError as e:
            msg = f"Configuration validation error: {str(e)}"
            logger.error(msg)
            self.unit.status = BlockedStatus(msg)
            return

        if env_config is None:
            logger.debug("Ingress hasn't been configured yet, waiting")
            event.defer()
            return
        pebble_config = self._make_pebble_config(env_config)
        nginx_config = self._make_nginx_config(env_config)
        exporter_config = self._get_nginx_prometheus_exporter_pebble_config()

        container = self.unit.get_container(CONTAINER_NAME)
        if container.can_connect():
            msg = "Updating Nginx site config"
            logger.info(msg)
            self.unit.status = MaintenanceStatus(msg)
            container.push("/etc/nginx/sites-enabled/default", nginx_config)
            container.make_dir(CACHE_PATH, make_parents=True)

            services = container.get_plan().to_dict().get("services", {})
            if services != pebble_config["services"]:
                msg = "Updating pebble layer config"
                logger.info(msg)
                self.unit.status = MaintenanceStatus(msg)
                container.add_layer(CONTAINER_NAME, pebble_config, combine=True)
                container.add_layer(EXPORTER_CONTAINER_NAME, exporter_config, combine=True)
                container.pebble.replan_services()
        else:
            self.unit.status = WaitingStatus("Waiting for Pebble to start")
            event.defer()
            return

        msg = "Ready"
        logger.info(msg)
        self.unit.status = ActiveStatus(msg)

    def _generate_keys_zone(self, name):
        """Generate hashed name to be used by Nginx's key zone.

        Args:
            name: Site name to be encoded.

        Returns:
            A hashed name to be used by Nginx's key zone.
        """
        hashed_value = hashlib.md5(name.encode("UTF-8"), usedforsecurity=False)
        hashed_name = hashed_value.hexdigest()[0:12]
        return f"{hashed_name}-cache"

    def _get_nginx_prometheus_exporter_pebble_config(self) -> ops.pebble.LayerDict:
        """Generate pebble config for the nginx-prometheus-exporter container.

        Returns:
            Pebble layer config for the nginx-prometheus-exporter layer.
        """
        return {
            "summary": "Nginx prometheus exporter",
            "description": "Prometheus exporter for nginx",
            "services": {
                EXPORTER_CONTAINER_NAME: {
                    "override": "replace",
                    "summary": "Nginx Prometheus Exporter",
                    "command": (
                        "nginx-prometheus-exporter"
                        f" -nginx.scrape-uri=http://localhost:{CONTAINER_PORT}/stub_status"
                    ),
                    "startup": "enabled",
                    "requires": [CONTAINER_NAME],
                },
            },
            "checks": {
                "nginx-exporter-up": {
                    "override": "replace",
                    "level": "alive",
                    "http": {"url": "http://localhost:9113/metrics"},
                },
            },
        }

    def _make_ingress_config(self) -> dict:
        """Return an assembled K8s ingress.

        Returns:
            An Ingress config dict.
        """
        config = self.model.config

        ingress = {
            "service-hostname": "mysite.local",
            "service-name": self.app.name,
            "service-port": CONTAINER_PORT,
        }

        site = config.get("site")

        relation = self.model.get_relation("nginx-proxy")
        if relation:
            # in case the relation app is not available yet
            prev_site = site
            site = relation.data[relation.app].get("service-hostname", prev_site)

        if site:
            ingress["service-hostname"] = site

        client_max_body_size = config.get("client_max_body_size")
        if client_max_body_size:
            ingress["max-body-size"] = client_max_body_size

        tls_secret_name = config.get("tls_secret_name")
        if tls_secret_name:
            ingress["tls-secret-name"] = tls_secret_name

        return ingress

    def _make_env_config(self, domain="svc.cluster.local") -> dict:  # noqa: C901
        """Return dict to be used as as runtime environment variables.

        Args:
            domain: domain used for the content-cache

        Returns:
            Charm's environment config

        Raises:
            ValueError: If proxy_cache_lock_age or proxy_cache_lock_timeout have invalid format.
        """
        config = self.model.config
        relation = self.model.get_relation("nginx-proxy")
        if relation and relation.data[relation.app] and relation.units:
            if any(
                relation.data[relation.app].get(nginx_config) is None
                for nginx_config in REQUIRED_INGRESS_RELATION_FIELDS
            ):
                return None
            site = relation.data[relation.app].get("service-hostname")
            svc_name = relation.data[relation.app].get("service-name")
            svc_port = relation.data[relation.app].get("service-port")
            backend_site_name = relation.data[relation.app].get("service-hostname")
            clients = []
            for peer in relation.units:
                unit_name = peer.name.replace("/", "-")
                service_url = f"{unit_name}.{svc_name}-endpoints.{self.model.name}.{domain}"
                clients.append(f"http://{service_url}:{svc_port}")
            # XXX: Will need to deal with multiple units at some point
            backend = clients[0]
        elif relation:
            return None
        else:
            backend = config["backend"]
            backend_site_name = config.get("backend_site_name")
            if not backend_site_name:
                backend_site_name = urlparse(backend).hostname
            site = config.get("site") if config.get("site") else self.app.name

        cache_all_configs = ""
        if not config["cache_all"]:
            cache_all_configs = "proxy_ignore_headers Cache-Control Expires"

        client_max_body_size = config["client_max_body_size"]

        proxy_cache_revalidate = "off"
        if config.get("proxy_cache_revalidate", False):
            proxy_cache_revalidate = "on"

        proxy_cache_lock = "off"
        if config.get("proxy_cache_lock", False):
            proxy_cache_lock = "on"

        # Validate time format for proxy_cache_lock configuration options
        proxy_cache_lock_age = config.get("proxy_cache_lock_age", "5s")
        proxy_cache_lock_timeout = config.get("proxy_cache_lock_timeout", "5s")

        try:
            validate_nginx_time(proxy_cache_lock_age, "proxy_cache_lock_age")
            validate_nginx_time(proxy_cache_lock_timeout, "proxy_cache_lock_timeout")
        except ValueError as e:
            logger.error("Configuration validation error: %s", str(e))
            raise

        env_config = {
            "CONTAINER_PORT": CONTAINER_PORT,
            "CONTENT_CACHE_BACKEND": backend,
            "CONTENT_CACHE_SITE": site,
            # https://bugs.launchpad.net/juju/+bug/1894782
            "JUJU_POD_NAME": self.unit.name,
            "JUJU_POD_NAMESPACE": self.model.name,
            "JUJU_POD_SERVICE_ACCOUNT": self.app.name,
            # Include nginx / charm configs as environment variables
            # to pass to the pebble services and ensure it restarts
            # nginx on changes.
            "NGINX_BACKEND": backend,
            "NGINX_CACHE_ALL": cache_all_configs,
            "NGINX_BACKEND_SITE_NAME": backend_site_name,
            "NGINX_CACHE_INACTIVE_TIME": config.get("cache_inactive_time", "10m"),
            "NGINX_CACHE_LOCK": proxy_cache_lock,
            "NGINX_CACHE_LOCK_AGE": proxy_cache_lock_age,
            "NGINX_CACHE_LOCK_TIMEOUT": proxy_cache_lock_timeout,
            "NGINX_CACHE_MAX_SIZE": config.get("cache_max_size", "10G"),
            "NGINX_CACHE_PATH": CACHE_PATH,
            "NGINX_CACHE_REVALIDATE": proxy_cache_revalidate,
            "NGINX_CACHE_USE_STALE": config["cache_use_stale"],
            "NGINX_CACHE_VALID": config["cache_valid"],
            "NGINX_CLIENT_MAX_BODY_SIZE": client_max_body_size,
            "NGINX_KEYS_ZONE": self._generate_keys_zone(site),
            "NGINX_SITE_NAME": site,
        }

        return env_config

    def _make_pebble_config(self, env_config) -> ops.pebble.PlanDict:
        """Generate our pebble config layer.

        Args:
            env_config: Charm's environment config

        Returns:
            content-cache container pebble layer config
        """
        pebble_config = {
            "summary": "content-cache layer",
            "description": "Pebble config layer for content-cache",
            "services": {
                CONTAINER_NAME: {
                    "override": "replace",
                    "summary": "content-cache",
                    "command": "/srv/content-cache/entrypoint.sh",
                    "startup": "enabled",
                    "environment": env_config,
                },
            },
            "checks": {
                CONTAINER_NAME: {
                    "override": "replace",
                    "exec": {"command": "ps -A | grep nginx"},
                    "threshold": 1,
                }
            },
        }
        return pebble_config

    def _make_nginx_config(self, env_config: dict) -> str:
        """Grab the NGINX template and fill it with our env config.

        Args:
            env_config: Charm's environment config

        Returns:
            A fully configured NGINX conf file
        """
        with open("content-cache_rock/nginx_cfg.tmpl", "r", encoding="utf-8") as file:
            content = file.read()

        nginx_config = content.format(**env_config)
        return nginx_config

    def _missing_charm_configs(self) -> list[str]:
        """Check and return list of required but missing configs.

        Returns:
            Missing settings in the required juju configs.
        """
        relation = self.model.get_relation("nginx-proxy")
        if relation:
            return []
        config = self.model.config
        missing = [
            setting
            for setting in REQUIRED_JUJU_CONFIGS
            if setting not in config or not config[setting]
        ]

        return sorted(missing)


if __name__ == "__main__":  # pragma: no cover
    main(ContentCacheCharm, use_juju_for_storage=True)
