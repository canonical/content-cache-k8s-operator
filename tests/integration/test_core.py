# Copyright 2022 Canonical Ltd.
# see LICENCE file for details.

import secrets

import pytest
import pytest_operator.plugin
import requests
import swiftclient
import swiftclient.exceptions
import swiftclient.service
from ops.model import Application


@pytest.mark.asyncio
async def test_openstack_object_storage_plugin(
    ops_test: pytest_operator.plugin.OpsTest,
    unit_ip_list,
    openstack_environment,
    app: Application
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
    except swiftclient.exceptions.ClientException as e:
        if e.http_status == 404:
            container_exists = False
        else:
            raise e
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
        assert any(
            filename in f for f in swift_object_list
        ), "media file uploaded should be stored in swift object storage"
        response = requests.get(f"{swift_conn.url}/{container}/{filename}")
        assert (
            response.status_code == 200
        ), "the image should be accessible from the swift server"
        assert response.text == content