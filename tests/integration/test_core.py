# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration test module."""

import re
import secrets
from typing import List

import juju.action
import pytest
import pytest_operator.plugin
import requests
import swiftclient
import swiftclient.exceptions
import swiftclient.service
from ops.model import ActiveStatus, Application


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
async def test_active(app: Application):
    """
    arrange: given charm has been built, deployed and related to a dependent application
    act: when the status is checked
    assert: then the workload status is active.
    """
    assert app.units[0].workload_status == ActiveStatus.name


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
async def test_any_app_reachable(ingress_ip: str):
    """
    arrange: given charm is deployed and related with any-app and nginx-integrator
    act: when the dependent application is queried via the ingress
    assert: then the response is HTTP 200 OK.
    """
    response = requests.get(f"http://{ingress_ip}", headers={"Host": "any-app"}, timeout=5)

    assert response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
async def test_an_app_cache_header(ingress_ip: str):
    """
    arrange: given charm is deployed, related with any-app and nginx-integrator
        and is reachable
    act: when the dependent application is queried via the ingress
    assert: then the response is HTTP 200 OK, has X-Cache-Status http header
        and contains description with content-cache-k8s'
    """
    response = requests.get(f"http://{ingress_ip}", headers={"Host": "any-app"}, timeout=5)

    assert response.status_code == 200
    assert "X-Cache-Status" in response.headers
    assert "content-cache-k8s" in response.headers["X-Cache-Status"]


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
async def test_unit_reachable(unit_ip_list: List):
    """
    arrange: given charm has been built, deployed and related to a dependent application
    act: when the dependent application is queried via the unit
    assert: then the response is HTTP 200 OK.
    """
    # Check we are querying at least one unit.
    assert len(unit_ip_list) > 0

    for unit_ip in unit_ip_list:
        response = requests.get(f"http://{unit_ip}:8080", timeout=5)

        assert response.status_code == 200


async def test_report_visits_by_ip(app: Application):
    """
    arrange: given that the gunicorn application is deployed and related to another charm
    act: when report-visits-by-ip is ran
    assert: the action result is successful and returns the expected output
    """
    action: juju.action.Action = await app.units[0].run_action("report-visits-by-ip")
    await action.wait()
    assert action.status == "completed"
    ip_regex = r"[0-9]+(?:\.[0-9]+){3}"
    ip_address_list = re.search(ip_regex, action.results["ips"])
    assert ip_address_list


@pytest.mark.asyncio
async def test_openstack_object_storage_plugin(
    ops_test: pytest_operator.plugin.OpsTest,
    unit_ip_list,
    openstack_environment,
    app: Application,
):
    """
    arrange: after charm deployed and openstack swift server ready.
    act: update charm configuration for openstack object storage plugin.
    assert: a file should be uploaded to the openstack server and be accesibe through it.
    """
    swift_conn = swiftclient.Connection(
        authurl=openstack_environment["OS_AUTH_URL"],
        auth_version="3",
        user=openstack_environment["OS_USERNAME"],
        key=openstack_environment["OS_PASSWORD"],
        os_options={
            "user_domain_name": openstack_environment["OS_USER_DOMAIN_ID"],
            "project_domain_name": openstack_environment["OS_PROJECT_DOMAIN_ID"],
            "project_name": openstack_environment["OS_PROJECT_NAME"],
        },
    )
    container_exists = True
    container = "content-cache"
    try:
        swift_conn.head_container(container)
    except swiftclient.exceptions.ClientException as exception:
        if exception.http_status != 404:
            raise exception
        container_exists = False
    if container_exists:
        for swift_object in swift_conn.get_container(container, full_listing=True)[1]:
            swift_conn.delete_object(container, swift_object["name"])
        swift_conn.delete_container(container)
    swift_conn.put_container(container)
    app = ops_test.model.applications["content-cache-k8s"]
    await app.set_config({"backend": f"http://{swift_conn.url}:80"})
    await app.set_config({"site": swift_conn.url})
    swift_service = swiftclient.service.SwiftService(
        options=dict(
            auth_version="3",
            os_auth_url=openstack_environment["OS_AUTH_URL"],
            os_username=openstack_environment["OS_USERNAME"],
            os_password=openstack_environment["OS_PASSWORD"],
            os_project_name=openstack_environment["OS_PROJECT_NAME"],
            os_project_domain_name=openstack_environment["OS_PROJECT_DOMAIN_ID"],
        )
    )
    swift_service.post(container=container, options={"read_acl": ".r:*,.rlistings"})
    for idx, unit_ip in enumerate(unit_ip_list):
        nonce = secrets.token_hex(8)
        filename = f"{nonce}.{unit_ip}.{idx}"
        content = "test-content"
        swift_conn.put_object(container=container, obj=filename, contents=content)
        swift_object_list = [
            o["name"] for o in swift_conn.get_container(container, full_listing=True)[1]
        ]
        assert any(filename in f for f in swift_object_list), (
            "media file uploaded should be stored in swift object storage"
        )
        response = requests.get(f"{swift_conn.url}/{container}/{filename}", timeout=5)
        assert response.status_code == 200, "the image should be accessible from the swift server"
        assert response.text == content
