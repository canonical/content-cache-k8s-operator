# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""General configuration module for integration tests."""

import configparser
import json
import re
from pathlib import Path
from typing import List

import jubilant
import jubilant.statustypes
import pytest_jubilant
import yaml
from pytest import Config, fixture


@fixture(scope="module")
def metadata():
    """Provide charm metadata."""
    yield yaml.safe_load(Path("./metadata.yaml").read_text())


@fixture(scope="module")
def app_name(metadata):
    """Provide app name from the metadata."""
    yield metadata["name"]


@fixture(scope="module")
def openstack_environment(request):
    """Parse the openstack rc style configuration file from the --openstack-rc argument.

    Return a dictionary of environment variables and values.
    """
    rc_file = request.config.getoption("--openstack-rc")
    rc_file = Path(rc_file).read_text()
    rc_file = re.sub("^export ", "", rc_file, flags=re.MULTILINE)
    openstack_conf = configparser.ConfigParser()
    openstack_conf.read_string(f"[DEFAULT]\n{rc_file}")
    return {k.upper(): v for k, v in openstack_conf["DEFAULT"].items()}


@fixture(scope="module")
def content_cache_image(pytestconfig: Config):
    """Get the content-cache image."""
    value: None | str = pytestconfig.getoption("--content-cache-image")
    assert value is not None, "please specify the --content-cache-image command line option"
    return value


@fixture(scope="function")
def unit_ip_list(juju: jubilant.Juju, app_name: str) -> List[str]:
    """Return ip addresses of current units."""
    status = juju.status()
    units = status.apps[app_name].units
    return [
        units[key].address for key in sorted(units.keys(), key=lambda n: int(n.split("/")[-1]))
    ]


@fixture(scope="module")
def nginx_integrator_app(juju: jubilant.Juju) -> str:
    """Deploy nginx-ingress-integrator charm and return its application name."""
    nginx_integrator_app_name = "nginx-ingress-integrator"
    juju.deploy(nginx_integrator_app_name, trust=True)
    juju.wait(
        lambda s: jubilant.all_active(s, nginx_integrator_app_name)
        or jubilant.all_waiting(s, nginx_integrator_app_name)
    )
    return nginx_integrator_app_name


@fixture(scope="module")
def charm_file(pytestconfig: Config) -> str:
    """Return the charm file path, packing it if not provided via --charm-file."""
    charm_file = pytestconfig.getoption("--charm-file")
    if charm_file:
        return charm_file
    return str(pytest_jubilant.pack())


@fixture(scope="module")
def app(
    juju: jubilant.Juju,
    app_name: str,
    charm_file: str,
    content_cache_image: str,
    nginx_integrator_app: str,
) -> str:
    """Deploy and relate content-cache-k8s for integration testing.

    Deploys any-charm as a backend, builds and deploys content-cache-k8s, then
    creates the nginx-proxy and nginx-route relations.
    """
    any_app_name = "any-app"
    ingress_lib = Path("lib/charms/nginx_ingress_integrator/v0/nginx_route.py").read_text()
    any_charm_script = Path("tests/integration/any_charm.py").read_text()

    any_charm_src_overwrite = {
        "nginx_route.py": ingress_lib,
        "any_charm.py": any_charm_script,
    }

    juju.deploy(
        "any-charm",
        app=any_app_name,
        channel="beta",
        config={"src-overwrite": json.dumps(any_charm_src_overwrite)},
    )
    juju.wait(lambda s: jubilant.all_active(s, any_app_name), timeout=600)
    juju.run(f"{any_app_name}/0", "rpc", {"method": "start_server"})
    juju.wait(lambda s: jubilant.all_active(s, any_app_name))

    juju.deploy(
        charm_file,
        app=app_name,
        resources={"content-cache-image": content_cache_image},
    )
    # content-cache-k8s starts in blocked state until the nginx-proxy relation is added
    juju.wait(
        lambda s: app_name in s.apps
        and (jubilant.all_active(s, app_name) or jubilant.all_blocked(s, app_name))
    )

    apps = [app_name, nginx_integrator_app, any_app_name]
    juju.integrate(f"{any_app_name}:nginx-route", f"{app_name}:nginx-proxy")
    juju.integrate(nginx_integrator_app, f"{app_name}:nginx-route")
    juju.wait(lambda s: jubilant.all_active(s, *apps), timeout=600)

    status = juju.status()
    assert status.apps[app_name].units[f"{app_name}/0"].is_active
    assert status.apps[any_app_name].units[f"{any_app_name}/0"].is_active

    yield app_name


@fixture(scope="module")
def ip_address_list(juju: jubilant.Juju, app: str, nginx_integrator_app: str) -> List[str]:
    """Get ingress IP addresses from nginx-ingress-integrator unit status message.

    Example message: Ingress IP(s): 127.0.0.1, Service IP(s): 10.152.183.84
    """

    def _has_ingress_ip(status: jubilant.statustypes.Status) -> bool:
        app_status = status.apps.get(nginx_integrator_app)
        if app_status is None or not app_status.units:
            return False
        unit = next(iter(app_status.units.values()))
        return "Ingress IP(s)" in unit.workload_status.message

    juju.wait(_has_ingress_ip, timeout=100)

    status = juju.status()
    unit = next(iter(status.apps[nginx_integrator_app].units.values()))
    status_message = unit.workload_status.message
    ip_regex = r"[0-9]+(?:\.[0-9]+){3}"
    ip_list = re.findall(ip_regex, status_message)
    assert ip_list, f"could not find IP address in status message: {status_message}"
    return ip_list


@fixture(scope="module")
def ingress_ip(ip_address_list: List[str]) -> str:
    """First match is the ingress IP."""
    return ip_address_list[0]
