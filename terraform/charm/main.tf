# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

resource "juju_application" "content_cache_k8s" {
  name       = var.app_name
  model_uuid = var.model_uuid

  charm {
    name     = "content-cache-k8s"
    channel  = var.channel
    revision = var.revision
    base     = var.base
  }

  config      = var.config
  constraints = var.constraints
  resources   = var.resources
  units       = var.units
}
