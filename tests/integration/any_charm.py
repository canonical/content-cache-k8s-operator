# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""This code snippet is used to be loaded into any-charm which is used for integration tests."""
import os
import pathlib
import signal
import subprocess

from any_charm_base import AnyCharmBase
from ingress import IngressRequires


class AnyCharm(AnyCharmBase):
    """Execute a simple web-server charm to test the ingress-proxy relation"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ingress = IngressRequires(
            self,
            {"service-hostname": self.app.name, "service-name": self.app.name, "service-port": 80},
        )

    def update_ingress(self, ingress_config):
        self.ingress.update_config(ingress_config)

    @staticmethod
    def start_server(port: int = 80):
        """Start an HTTP server daemon."""
        www_dir = pathlib.Path("/tmp/www")
        www_dir.mkdir(exist_ok=True)
        ok_file = www_dir / "ok"
        ok_file.write_text("ok")
        # We create a pid file to avoid concurrent executions of the http server
        pid_file = pathlib.Path("/tmp/any.pid")
        if pid_file.exists():
            os.kill(int(pid_file.read_text()), signal.SIGKILL)
            pid_file.unlink()
        p = subprocess.Popen(
            ["python3", "-m", "http.server", "-d", www_dir, str(port)],
            start_new_session=True,
        )
        pid_file.write_text(str(p.pid))
        return port
