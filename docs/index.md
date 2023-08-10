A [Juju](https://juju.is/) [charm](https://juju.is/docs/olm/charmed-operators) deploying and managing service for caching content, built on top of [Nginx](https://www.nginx.com/), configurable to cache any http or https web site and useful for building content delivery networks (CDN).

This charm simplifies initial deployment and caching operations on Kubernetes, such as scaling the number of cache instances and cache configuration changes. It allows for deployment on many different Kubernetes platforms, from [MicroK8s](https://microk8s.io) to
[Charmed Kubernetes](https://ubuntu.com/kubernetes) and public cloud Kubernetes
offerings.

This service was developed to provide front-end caching for web sites run by Canonical's IS team, and to reduce the need for third-party CDNs by providing high-bandwidth access to web sites via this caching front-end.

Currently used for a number of services including [the Snap Store](https://snapcraft.io/store),
the majority of Canonical's web properties including [ubuntu.com](https://ubuntu.com) and
[canonical.com](https://canonical.com), and [Ubuntu Extended Security Maintenance](https://ubuntu.com/security/esm).

For DevOps or SRE teams this charm will make operating it simple and straightforward through Juju's clean interface.

# Navigation

| Level | Path | Navlink |
| -- | -- | -- |
| 1 | tutorial | [Tutorial]() |
| 2 | tutorial-getting-started | [Quick Guide](/t/content-cache-k8s-docs-quick-guide/8651) |
| 1 | how-to | [How to]() |
| 2 | how-to-contribute | [Contribute](/t/content-cache-k8s-docs-contributing/8617) |
| 2 | how-to-cache-content-with-openstack-swift | [Cache content with OpenStack/Swift storage](/t/content-cache-k8s-docs-content-cache-with-openstack-swift-storage/8619) |
| 1 | reference | [Reference]() |
| 2 | reference-actions | [Actions](/t/content-cache-k8s-docs-actions/8715) |
| 2 | reference-configurations | [Configurations](/t/content-cache-k8s-docs-configurations/8714) |
| 2 | reference-integrations | [Integrations](/t/content-cache-k8s-docs-integrations/8713) |
| 1 | explanation | [Explanation]() |
| 2 | explanation-charm-architecture | [Charm architecture](/t/content-cache-k8s-docs-charm-architecture/8712) |
