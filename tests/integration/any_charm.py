# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

# This Python script is designed to be loaded into any-charm. Some lint checks do not apply
# pylint: disable=import-error,consider-using-with,duplicate-code

"""This code snippet is used to be loaded into any-charm which is used for integration tests."""
import os
import pathlib
import signal
import subprocess

from any_charm_base import AnyCharmBase
from nginx_route import require_nginx_route


class AnyCharm(AnyCharmBase):
    """Execute a simple web-server charm to test the nginx-route relation."""

    def __init__(self, *args, **kwargs):
        """Init function for the class.

        Args:
            args: Variable list of positional arguments passed to the parent constructor.
            kwargs: Variable list of positional keyword arguments passed to the parent constructor.
        """
        super().__init__(*args, **kwargs)
        require_nginx_route(
            charm=self, service_hostname=self.app.name, service_name=self.app.name, service_port=80
        )

    def delete_nginx_route_relation_data(self, field: str) -> None:
        """Delete one data field from the nginx-route relation data.

        Args:
            field: the name of the field to be deleted.
        """
        relation = self.model.get_relation("nginx-route")
        del relation.data[self.app][field]

    @staticmethod
    def start_server(port: int = 80):
        """Start an HTTP server daemon.

        Args:
            port: The port where the server is connected.

        Returns:
            The port where the server is connected.
        """
        www_dir = pathlib.Path("/tmp/www")
        www_dir.mkdir(exist_ok=True)
        (www_dir / "ok").write_text("ok")
        # We create a pid file to avoid concurrent executions of the http server
        pid_file = pathlib.Path("/tmp/any.pid")
        if pid_file.exists():
            os.kill(int(pid_file.read_text(encoding="utf8")), signal.SIGKILL)
            pid_file.unlink()
        log_file_object = pathlib.Path("/tmp/any.log").open("wb+")
        proc_http = subprocess.Popen(
            ["python3", "-m", "http.server", "-d", www_dir, str(port)],
            start_new_session=True,
            stdout=log_file_object,
            stderr=log_file_object,
        )
        pid_file.write_text(str(proc_http.pid), encoding="utf8")
        return port
