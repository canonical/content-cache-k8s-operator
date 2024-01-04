A [Juju](https://juju.is/) [charm](https://juju.is/docs/olm/charmed-operators) deploying and managing service for caching content, built on top of [Nginx](https://www.nginx.com/), configurable to cache any http or https web site and useful for building content delivery networks (CDN).

This charm simplifies initial deployment and caching operations on Kubernetes, such as scaling the number of cache instances and cache configuration changes. It allows for deployment on many different Kubernetes platforms, from [MicroK8s](https://microk8s.io) to
[Charmed Kubernetes](https://ubuntu.com/kubernetes) and public cloud Kubernetes
offerings.

This service was developed to provide front-end caching for web sites run by Canonical's IS team, and to reduce the need for third-party CDNs by providing high-bandwidth access to web sites via this caching front-end.

Currently used for a number of services including [the Snap Store](https://snapcraft.io/store),
the majority of Canonical's web properties including [ubuntu.com](https://ubuntu.com) and
[canonical.com](https://canonical.com), and [Ubuntu Extended Security Maintenance](https://ubuntu.com/security/esm).

For DevOps or SRE teams this charm will make operating it simple and straightforward through Juju's clean interface.

# Contents

1. [Explanation](explanation)
  1. [Charm architecture](explanation/charm-architecture.md)
1. [How To](how-to)
  1. [Cache content with OpenStack/Swift storage](how-to/cache-content-with-openstack-swift.md)
  1. [How to contribute](how-to/contribute.md)
1. [Reference](reference)
  1. [Actions](reference/actions.md)
  1. [Configurations](reference/configurations.md)
  1. [External access](reference/external-access.md)
  1. [Integrations](reference/integrations.md)
1. [Tutorial](tutorial)
  1. [Quick guide](tutorial/getting-started.md)