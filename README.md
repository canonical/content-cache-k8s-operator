[![CharmHub Badge](https://charmhub.io/content-cache-k8s/badge.svg)](https://charmhub.io/content-cache-k8s)
[![Publish to edge](https://github.com/canonical/content-cache-k8s-operator/actions/workflows/publish_charm.yaml/badge.svg)](https://github.com/canonical/content-cache-k8s-operator/actions/workflows/publish_charm.yaml)
[![Promote charm](https://github.com/canonical/content-cache-k8s-operator/actions/workflows/promote_charm.yaml/badge.svg)](https://github.com/canonical/content-cache-k8s-operator/actions/workflows/promote_charm.yaml)
[![Discourse Status](https://img.shields.io/discourse/status?server=https%3A%2F%2Fdiscourse.charmhub.io&style=flat&label=CharmHub%20Discourse)](https://discourse.charmhub.io)

# Content Cache Operator

A [Juju](https://juju.is/) [charm](https://juju.is/docs/olm/charmed-operators) deploying and managing service for caching content on Kubernetes, built on top of [Nginx](https://www.nginx.com/), configurable to cache any http or https web site and useful for building Content Delivery Networks (CDN).

Like any Juju charm, this charm supports one-line deployment, configuration, integration, scaling, and more. For Charmed Content Cache, this includes:
* scaling the number of cache instances
* cache configuration changes
* deployment on many different Kubernetes platforms, from MicroK8s to Charmed Kubernetes and public cloud Kubernetes offerings

This service was developed to provide front-end caching for web sites run by
Canonical's IS (Infrastructure Services) team, and to reduce the need for third-party CDNs by providing
high-bandwidth access to web sites via this caching front-end. Currently used
for a number of services including [the Snap Store](https://snapcraft.io/store),
the majority of Canonical's web properties including [ubuntu.com](https://ubuntu.com) and
[canonical.com](https://canonical.com), and [Ubuntu Extended Security Maintenance](https://ubuntu.com/security/esm).

This Kubernetes-based version is built using the same approach as the [machine content-cache charm](https://charmhub.io/content-cache), and can be used as a front-end caching service in
a situation where your Kubernetes cluster and its ingress controllers have
a fast connection to the Internet.

For information about how to deploy, integrate, and manage this charm, see the Official [Content Cache Documentation](https://charmhub.io/content-cache-k8s/docs).

## Get started

To begin, refer to the [Content Cache tutorial](https://charmhub.io/content-cache-k8s/docs/tutorial-getting-started) for step-by-step instructions.

### Basic operations

The following actions are available for the charm:
- report-visits-by-ip

Tuning options include:
- cache storage size
- maximum request size to cache 
- cache validity duration

You can find more information about supported actions in [the Charmhub documentation](https://charmhub.io/content-cache-k8s/actions).

## Integrations

Content-cache is meant to serve as cache for another charm. You can use Hello-kubecon as an example:

```
juju deploy content-cache-k8s
juju deploy hello-kubecon
juju relate content-cache-k8s:ingress-proxy hello-kubecon
```

Apart from this integration, the charm can be integrated with other Juju charms and services as well. You can find the full list of integrations in [the Charmhub documentation](https://charmhub.io/content-cache-k8s/integrations).


## Learn more

- [Read more](https://charmhub.io/content-cache-k8s/docs)
- [Developer documentation](https://nginx.org/en/docs/dev/development_guide.html)
- [Official webpage](https://www.nginx.com/)
- [Troubleshooting](https://matrix.to/#/#charmhub-charmdev:ubuntu.com)


## Project and community

The Content-cache-k8s Operator is a member of the Ubuntu family. It is an
open source project that warmly welcomes community projects, contributions,
suggestions, fixes and constructive feedback.
* [Code of conduct](https://ubuntu.com/community/code-of-conduct)
* [Get support](https://discourse.charmhub.io/)
* [Contribute](https://charmhub.io/content-cache-k8s/docs/how-to-contribute)
* [Matrix](https://matrix.to/#/#charmhub-charmdev:ubuntu.com)
