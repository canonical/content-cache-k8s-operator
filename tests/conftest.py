# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""General configuration module for tests."""
import pytest


def pytest_addoption(parser: pytest.Parser):
    """Process parameters for integration tests.

    Args:
        parser: Pytest parser used to add arguments to console commands
    """
    # --openstack-rc points to an openstack credential file in the "rc" file style
    # Here's an example of that file
    # $ echo ~/openrc
    # export OS_REGION_NAME=RegionOne
    # export OS_PROJECT_DOMAIN_ID=default
    # export OS_AUTH_URL=http://10.0.0.1/identity
    # export OS_TENANT_NAME=demo
    # export OS_USER_DOMAIN_ID=default
    # export OS_USERNAME=demo
    # export OS_VOLUME_API_VERSION=3
    # export OS_AUTH_TYPE=password
    # export OS_PROJECT_NAME=demo
    # export OS_PASSWORD=nomoresecret
    # export OS_IDENTITY_API_VERSION=3
    parser.addoption("--charm-file", action="store")
    parser.addoption("--openstack-rc", action="store", default="")
    parser.addoption("--content-cache-image", action="store", default="")
