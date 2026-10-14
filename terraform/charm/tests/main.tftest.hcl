# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

run "setup_tests" {
  module {
    source = "./tests/setup"
  }
}

run "basic_deploy" {
  variables {
    model_uuid = run.setup_tests.model_uuid
    base       = "ubuntu@22.04"
    channel    = "latest/edge"
    # renovate: depName="content-cache-k8s"
    revision = 123
  }

  assert {
    condition     = output.application.name == "content-cache-k8s"
    error_message = "content-cache-k8s application name did not match expected"
  }

  assert {
    condition     = output.provides.value.endpoint == "grafana-dashboard"
    error_message = "content-cache-k8s module should provide 'provides.value' output"
  }

  assert {
    condition     = output.provides.metrics_endpoint.endpoint == "metrics-endpoint"
    error_message = "content-cache-k8s module should provide 'provides.metrics_endpoint' output"
  }

  assert {
    condition     = output.provides.nginx_proxy.endpoint == "nginx-proxy"
    error_message = "content-cache-k8s module should provide 'provides.nginx_proxy' output"
  }

  assert {
    condition     = output.requires.value.endpoint == "logging"
    error_message = "content-cache-k8s module should provide 'requires.value' output"
  }

  assert {
    condition     = output.requires.nginx_route.endpoint == "nginx-route"
    error_message = "content-cache-k8s module should provide 'requires.nginx_route' output"
  }
}
