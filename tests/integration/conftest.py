# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""General configuration module for integration tests."""
import configparser
import json
import re
from pathlib import Path
from typing import Any, Awaitable, Callable, List

import pytest_asyncio
import yaml
from juju.errors import JujuAppError, JujuUnitError
from ops.model import ActiveStatus, Application
from pytest import Config, fixture
from pytest_operator.plugin import OpsTest


@fixture(scope="module")
def metadata():
    """Provide charm metadata."""
    yield yaml.safe_load(Path("./metadata.yaml").read_text())


@fixture(scope="module")
def app_name(metadata):
    """Provide app name from the metadata."""
    yield metadata["name"]


@fixture(scope="module")
def run_action(ops_test: OpsTest) -> Callable[[str, str], Awaitable[Any]]:
    """Create a async function to run action and return results."""

    async def _run_action(application_name: str, action_name: str, **params):
        """Run a specified action.

        Args:
            application_name: Name the application is deployed with.
            action_name: Name of the action to be executed.
            params: Dictionary with action parameters.

        Returns:
            The results of the executed action
        """
        application = ops_test.model.applications[application_name]
        action = await application.units[0].run_action(action_name, **params)
        await action.wait()
        return action.results

    return _run_action


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


@pytest_asyncio.fixture(scope="function")
async def get_unit_ip_list(ops_test: OpsTest, app_name: str):
    """Retrieve unit ip addresses, similar to fixture_get_unit_status_list."""

    async def get_unit_ip_list_action():
        """Extract the IPs from juju units.

        Returns:
            A list of IPs of the juju units in the model.
        """
        status = await ops_test.model.get_status()
        units = status.applications[app_name].units
        ip_list = [
            units[key].address for key in sorted(units.keys(), key=lambda n: int(n.split("/")[-1]))
        ]
        return ip_list

    yield get_unit_ip_list_action


@pytest_asyncio.fixture(scope="function")
async def unit_ip_list(get_unit_ip_list):
    """Yield ip addresses of current units."""
    yield await get_unit_ip_list()


@pytest_asyncio.fixture(scope="module")
async def nginx_integrator_app(ops_test: OpsTest):
    """Deploy nginx-ingress-integrator charm."""
    nginx_integrator_app_name = "nginx-ingress-integrator"
    nginx_integrator_app = await ops_test.model.deploy(nginx_integrator_app_name, trust=True)
    await ops_test.model.wait_for_idle()
    assert (
        ops_test.model.applications[nginx_integrator_app_name].units[0].workload_status
        == ActiveStatus.name
    )
    yield nginx_integrator_app


@fixture(scope="module")
def charm_file(pytestconfig: Config):
    """Get the existing charm file."""
    value = pytestconfig.getoption("--charm-file")
    yield f"./{value}"


@pytest_asyncio.fixture(scope="module")
async def app(
    ops_test: OpsTest,
    app_name: str,
    charm_file: str,
    content_cache_image: str,
    nginx_integrator_app: Application,
    run_action,
):
    """Content-cache-k8s charm used for integration testing.

    Deploy any-charm charm, builds the charm and deploys it for testing purposes.
    """
    any_app_name = "any-app"
    ingress_lib = Path("lib/charms/nginx_ingress_integrator/v0/nginx_route.py").read_text()
    any_charm_script = Path("tests/integration/any_charm.py").read_text()

    any_charm_src_overwrite = {
        "nginx_route.py": ingress_lib,
        "any_charm.py": any_charm_script,
    }

    await ops_test.model.deploy(
        "any-charm",
        application_name=any_app_name,
        channel="beta",
        config={"src-overwrite": json.dumps(any_charm_src_overwrite)},
    )
    await run_action(any_app_name, "rpc", method="start_server")
    await ops_test.model.wait_for_idle(status="active")

    application = await ops_test.model.deploy(
        charm_file,
        application_name=app_name,
        resources={
            "content-cache-image": content_cache_image,
        },
        series="jammy",
    )

    try:
        await ops_test.model.wait_for_idle(raise_on_blocked=True)
    except (JujuAppError, JujuUnitError):
        print("BlockedStatus raised: will be solved after relation nginx-proxy")

    apps = [app_name, nginx_integrator_app.name, any_app_name]
    await ops_test.model.add_relation(any_app_name, f"{app_name}:nginx-proxy")
    await ops_test.model.wait_for_idle(apps=apps, status=ActiveStatus.name, timeout=60 * 5)
    await ops_test.model.add_relation(nginx_integrator_app.name, f"{app_name}:nginx-route")
    await ops_test.model.wait_for_idle(apps=apps, status=ActiveStatus.name, timeout=60 * 5)

    assert ops_test.model.applications[app_name].units[0].workload_status == ActiveStatus.name
    assert ops_test.model.applications[any_app_name].units[0].workload_status == ActiveStatus.name

    yield application


@pytest_asyncio.fixture(scope="module")
async def ip_address_list(ops_test: OpsTest, app: Application, nginx_integrator_app: Application):
    """Get unit IP address from workload message.

    Example: Ingress IP(s): 127.0.0.1, Service IP(s): 10.152.183.84
    """
    # Reduce the update_status frequency until the cluster is deployed
    async with ops_test.fast_forward():
        await ops_test.model.block_until(
            lambda: "Ingress IP(s)" in nginx_integrator_app.units[0].workload_status_message,
            timeout=100,
        )
    nginx_integrator_unit = nginx_integrator_app.units[0]
    status_message = nginx_integrator_unit.workload_status_message
    ip_regex = r"[0-9]+(?:\.[0-9]+){3}"
    ip_address_list = re.findall(ip_regex, status_message)
    assert ip_address_list, f"could not find IP address in status message: {status_message}"
    yield ip_address_list


@pytest_asyncio.fixture(scope="module")
async def ingress_ip(ip_address_list: List):
    """First match is the ingress IP."""
    yield ip_address_list[0]


@pytest_asyncio.fixture(scope="module")
async def service_ip(ip_address_list: List):
    """Last match is the service IP."""
    yield ip_address_list[-1]
