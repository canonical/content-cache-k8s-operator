# Copyright 2022 Canonical Ltd.
# Licensed under the GPLv3, see LICENCE file for details.

import secrets

import pytest
import pytest_operator.plugin
import requests
import swiftclient
import swiftclient.exceptions
import swiftclient.service


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
async def test_build_and_deploy(
    ops_test: pytest_operator.plugin.OpsTest, content_cache_image
):
    """
    arrange: no pre-condition.
    act: build charm using charmcraft and deploy charm to test juju model.
    assert: building and deploying should success and status should be "blocked" since the
        database info hasn't been provided yet.
    """
    my_charm = await ops_test.build_charm(".")
    await ops_test.model.deploy(
        my_charm,
        resources={"content-cache-image": content_cache_image},
        series="jammy",
    )
    await ops_test.model.wait_for_idle()


@pytest.mark.asyncio
async def test_openstack_object_storage_plugin(  # noqa: C901
    ops_test: pytest_operator.plugin.OpsTest,
    unit_ip_list,
    openstack_environment,
):
    """
    arrange: after charm deployed, db relation established and openstack swift server ready.
    act: update charm configuration for openstack object storage plugin.
    assert: openstack object storage plugin should be installed after the config update and
        WordPress openstack swift object storage integration should be set up properly.
        After openstack swift plugin activated, an image file uploaded to one unit through
        WordPress media uploader should be accessible from all units.
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
        for r in swift_service.upload(
            container=container,
            objects=[swiftclient.service.SwiftUploadObject(None, object_name=filename)],
        ):
            if r["success"]:
                if "object" in r:
                    print(r["object"])
                elif "for_object" in r:
                    print("%s segment %s" % (r["for_object"], r["segment_index"]))
            else:
                error = r["error"]
                if r["action"] == "create_container":
                    print(
                        "Warning: failed to create container " "'%s'%s",
                        container,
                        error,
                    )
                elif r["action"] == "upload_object":
                    print(
                        "Failed to upload object %s to container %s: %s"
                        % (container, r["object"], error)
                    )
                else:
                    print("%s" % error)
        swift_object_list = [
            o["name"] for o in swift_conn.get_container(container, full_listing=True)[1]
        ]
        print(swift_object_list)
        assert any(
            filename in f for f in swift_object_list
        ), "media file uploaded should be stored in swift object storage"
        assert (
            requests.get(f"{swift_conn.url}/{container}/{filename}").status_code == 200
        ), "the image should be accessible from the swift server"
        # assert (
        #     requests.get(f"{swift_conn.url}/{container}/{filename}").content == image_content
        # ), "image downloaded from swift server should match the image uploaded"
