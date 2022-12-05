#!/usr/bin/env python3

# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Charm for Content Cache on kubernetes."""
import hashlib
import logging
import re
from datetime import datetime, timedelta
from itertools import groupby
from urllib.parse import urlparse

from charms.nginx_ingress_integrator.v0.ingress import (
    IngressCharmEvents,
    IngressProxyProvides,
    IngressRequires,
)
from ops.charm import ActionEvent, CharmBase
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus, WaitingStatus

logger = logging.getLogger(__name__)

CACHE_PATH = "/var/lib/nginx/proxy/cache"
CONTAINER_NAME = "content-cache"
CONTAINER_PORT = 80
REQUIRED_JUJU_CONFIGS = ["site", "backend"]


class ContentCacheCharm(CharmBase):
    """Charm the service."""

    on = IngressCharmEvents()

    def __init__(self, *args):
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

        self.ingress_proxy_provides = IngressProxyProvides(self)
        self.ingress = IngressRequires(self, self._make_ingress_config())
        self.framework.observe(self.on.ingress_available, self._on_config_changed)

    def _on_content_cache_pebble_ready(self, event) -> None:
        """Handle content_cache_pebble_ready event and configure workload container."""
        msg = "Configuring workload container (content-cache-pebble-ready)"
        logger.info(msg)
        self.model.unit.status = MaintenanceStatus(msg)
        self.on.config_changed.emit()

    def _on_start(self, event) -> None:
        """Handle workload container started."""
        logger.info("Starting workload container (start)")
        self.model.unit.status = ActiveStatus("Started")

    def _on_config_changed(self, event) -> None:
        """Handle config_changed event and reconfigure workload container."""
        msg = "Configuring workload container (config-changed)"
        logger.info(msg)
        self.model.unit.status = MaintenanceStatus(msg)
        self.configure_workload_container(event)

    def _report_visits_by_ip_action(self, event: ActionEvent) -> None:
        """Handle the report-visits-by-ip action."""
        results = self._report_visits_by_ip(event)
        event.set_results({"ips": str(results)})

    def _report_visits_by_ip(self, _) -> list[(int, str)]:
        """Report requests to nginx grouped and ordered by IP and report action result."""
        container = self.unit.get_container(CONTAINER_NAME)
        log_path = "/var/log/nginx/access.log"
        with container.pull(log_path) as log_file:
            list_to_search = log_file.readlines()
        ip_regex = r"[0-9]+(?:\.[0-9]+){3}"
        ip_list = []
        current_datetime = datetime.now()
        start_datetime = current_datetime - timedelta(minutes=20)
        for line in list_to_search:
            line = line.split()
            log_datetime = datetime.strptime(line[3].lstrip("[").rstrip("]"), "%d/%b/%Y:%H:%M:%S")
            if log_datetime >= start_datetime and re.search(ip_regex, line[0]):
                ip_list.append(str(line[0]))
        return sorted(
            [(key, len(list(group))) for key, group in groupby(ip_list)], key=lambda t: t[1]
        )

    def _on_upgrade_charm(self, event) -> None:
        """Handle upgrade_charm event and reconfigure workload container."""
        msg = "Configuring workload container (upgrade-charm)"
        logger.info(msg)
        self.model.unit.status = MaintenanceStatus(msg)
        self.configure_workload_container(event)

    def configure_workload_container(self, event) -> None:
        """Configure/set up workload container inside pod."""
        missing = sorted(self._missing_charm_configs())
        if missing:
            msg = f"Required config(s) empty: {', '.join(missing)}"
            logger.warning(msg)
            self.unit.status = BlockedStatus(msg)
            return

        msg = "Assembling k8s ingress config"
        logger.info(msg)
        self.unit.status = MaintenanceStatus(msg)
        self.ingress.update_config(self._make_ingress_config())

        msg = "Assembling environment configs"
        logger.info(msg)
        self.unit.status = MaintenanceStatus(msg)
        env_config = self._make_env_config()

        msg = "Assembling pebble layer config"
        logger.info(msg)
        self.unit.status = MaintenanceStatus(msg)
        pebble_config = self._make_pebble_config(env_config)

        msg = "Assembling Nginx config"
        logger.info(msg)
        self.unit.status = MaintenanceStatus(msg)
        nginx_config = self._make_nginx_config(env_config)

        try:
            container = self.unit.get_container(CONTAINER_NAME)

            msg = "Updating Nginx site config"
            logger.info(msg)
            self.unit.status = MaintenanceStatus(msg)
            container.push("/etc/nginx/sites-available/default", nginx_config)
            with open("files/nginx-logging-format.conf", "r") as f:
                container.push("/etc/nginx/conf.d/nginx-logging-format.conf", f)
            container.make_dir(CACHE_PATH, make_parents=True)

            services = container.get_plan().to_dict().get("services", {})
            if services != pebble_config["services"]:

                msg = "Updating pebble layer config"
                logger.info(msg)
                self.unit.status = MaintenanceStatus(msg)
                container.add_layer(CONTAINER_NAME, pebble_config, combine=True)

                service = container.get_service(CONTAINER_NAME)
                if service.is_running():
                    msg = "Stopping content-cache"
                    logger.info(msg)
                    self.unit.status = MaintenanceStatus(msg)
                    container.stop(CONTAINER_NAME)

                msg = "Starting content-cache"
                logger.info(msg)
                self.unit.status = MaintenanceStatus(msg)
                container.start(CONTAINER_NAME)
        except ConnectionError:
            msg = "Pebble is not ready, deferring event"
            logger.info(msg)
            self.unit.status = WaitingStatus(msg)
            event.defer()
            return

        msg = "Ready"
        logger.info(msg)
        self.unit.status = ActiveStatus(msg)

    def _generate_keys_zone(self, name):
        """Generate hashed name to be used by Nginx's key zone."""
        hashed_value = hashlib.md5(name.encode("UTF-8"), usedforsecurity=False)
        hashed_name = hashed_value.hexdigest()[0:12]
        return f"{hashed_name}-cache"

    def _make_ingress_config(self) -> list:
        """Return an assembled K8s ingress."""
        config = self.model.config

        ingress = {
            "service-hostname": "mysite.local",
            "service-name": self.app.name,
            "service-port": CONTAINER_PORT,
        }

        site = config.get("site")

        relation = self.model.get_relation("ingress-proxy")
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

    def _make_env_config(self, domain="svc.cluster.local") -> dict:
        """Return dict to be used as as runtime environment variables."""
        config = self.model.config
        relation = self.model.get_relation("ingress-proxy")
        if relation:
            site = relation.data[relation.app]["service-hostname"]
            svc_name = relation.data[relation.app]["service-name"]
            svc_port = relation.data[relation.app]["service-port"]
            backend_site_name = relation.data[relation.app]["service-hostname"]
            clients = []
            for peer in relation.units:
                unit_name = peer.name.replace("/", "-")
                service_url = f"{unit_name}.{svc_name}-endpoints.{self.model.name}.{domain}"
                clients.append(f"http://{service_url}:{svc_port}")
            # XXX: Will need to deal with multiple units at some point
            backend = clients[0]
        else:
            backend = config["backend"]
            backend_site_name = config.get("backend_site_name")
            if not backend_site_name:
                backend_site_name = urlparse(backend).hostname
            site = config["site"]

        cache_all_configs = ""
        if not config["cache_all"]:
            cache_all_configs = "proxy_ignore_headers Cache-Control Expires"

        client_max_body_size = config["client_max_body_size"]

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
            "NGINX_CACHE_MAX_SIZE": config.get("cache_max_size", "10G"),
            "NGINX_CACHE_PATH": CACHE_PATH,
            "NGINX_CACHE_USE_STALE": config["cache_use_stale"],
            "NGINX_CACHE_VALID": config["cache_valid"],
            "NGINX_CLIENT_MAX_BODY_SIZE": client_max_body_size,
            "NGINX_KEYS_ZONE": self._generate_keys_zone(site),
            "NGINX_SITE_NAME": site,
        }

        return env_config

    def _make_pebble_config(self, env_config) -> dict:
        """Generate our pebble config layer."""
        pebble_config = {
            "summary": "content-cache layer",
            "description": "Pebble config layer for content-cache",
            "services": {
                CONTAINER_NAME: {
                    "override": "replace",
                    "summary": "content-cache",
                    "command": "/usr/sbin/nginx -g 'daemon off;'",
                    "startup": "false",
                    "environment": env_config,
                },
            },
        }
        return pebble_config

    def _make_nginx_config(self, env_config) -> str:
        with open("templates/nginx_cfg.tmpl", "r") as f:
            content = f.read()

        nginx_config = content.format(**env_config)
        return nginx_config

    def _missing_charm_configs(self) -> list:
        """Check and return list of required but missing configs."""
        relation = self.model.get_relation("ingress-proxy")
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
