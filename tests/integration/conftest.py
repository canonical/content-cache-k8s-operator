# Copyright 2022 Canonical Ltd.
# Licensed under the GPLv3, see LICENCE file for details.

import configparser
import re

import pytest
import pytest_asyncio
import pytest_operator.plugin


@pytest.fixture
def openstack_environment(request):
    """Parse the openstack rc style configuration file from the --openstack-rc argument

    Return a dictionary of environment variables and values.
    """
    rc_file = request.config.getoption("--openstack-rc")
    with open(rc_file) as f:
        rc_file = f.read()
    rc_file = re.sub("^export ", "", rc_file, flags=re.MULTILINE)
    openstack_conf = configparser.ConfigParser()
    openstack_conf.read_string("[DEFAULT]\n" + rc_file)
    return {k.upper(): v for k, v in openstack_conf["DEFAULT"].items()}


@pytest.fixture(scope="module")
def content_cache_image(pytestconfig: pytest.Config):
    """Get the content-cache image."""
    value: None | str = pytestconfig.getoption("--content-cache-image")
    assert (
        value is not None
    ), "please specify the --content-cache-image command line option"
    return value


@pytest_asyncio.fixture(scope="function", name="get_unit_ip_list")
async def fixture_get_unit_ip_list(ops_test: pytest_operator.plugin.OpsTest):
    """Helper function to retrieve unit ip addresses, similar to fixture_get_unit_status_list"""

    async def _get_unit_ip_list():
        status = await ops_test.model.get_status()
        units = status.applications["content-cache-k8s"].units
        ip_list = []
        for key in sorted(units.keys(), key=lambda n: int(n.split("/")[-1])):
            ip_list.append(units[key].address)
        return ip_list

    yield _get_unit_ip_list


@pytest_asyncio.fixture(scope="function", name="unit_ip_list")
async def fixture_unit_ip_list(get_unit_ip_list):
    """A fixture containing ip addresses of current units"""
    yield await get_unit_ip_list()
