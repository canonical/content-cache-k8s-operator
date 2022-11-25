# Copyright 2022 Canonical Ltd.
# see LICENCE file for details.

import configparser
import pathlib
import re

import pytest
import pytest_asyncio
import pytest_operator.plugin


@pytest.fixture
def openstack_environment(request):
    """Parse the openstack rc style configuration file from the --openstack-rc argument.

    Return a dictionary of environment variables and values.
    """
    rc_file = request.config.getoption("--openstack-rc")
    rc_file = pathlib.Path(rc_file).read_text()
    rc_file = re.sub("^export ", "", rc_file, flags=re.MULTILINE)
    openstack_conf = configparser.ConfigParser()
    openstack_conf.read_string(f"[DEFAULT]\n{rc_file}")
    return {k.upper(): v for k, v in openstack_conf["DEFAULT"].items()}


@pytest.fixture(scope="module")
def content_cache_image(pytestconfig: pytest.Config):
    """Get the content-cache image."""
    value: None | str = pytestconfig.getoption("--content-cache-image")
    assert value is not None, "please specify the --content-cache-image command line option"
    return value


@pytest_asyncio.fixture(scope="function")
async def get_unit_ip_list(ops_test: pytest_operator.plugin.OpsTest):
    """Helper function to retrieve unit ip addresses, similar to fixture_get_unit_status_list."""

    async def get_unit_ip_list_action():
        status = await ops_test.model.get_status()
        units = status.applications["content-cache-k8s"].units
        ip_list = [
            units[key].address for key in sorted(units.keys(), key=lambda n: int(n.split("/")[-1]))
        ]
        return ip_list

    yield get_unit_ip_list_action


@pytest_asyncio.fixture(scope="function")
async def unit_ip_list(get_unit_ip_list):
    """A fixture containing ip addresses of current units."""
    yield await get_unit_ip_list()


@pytest_asyncio.fixture(scope="module")
async def app(ops_test: pytest_operator.plugin.OpsTest, content_cache_image: str):
    """Content-cache-k8s charm used for integration testing.

    Builds the charm and deploys it for testing purposes.
    """
    my_charm = await ops_test.build_charm(".")
    application = await ops_test.model.deploy(
        my_charm,
        resources={"content-cache-image": content_cache_image},
        series="jammy",
    )
    await ops_test.model.wait_for_idle()

    yield application
