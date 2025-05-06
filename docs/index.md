A [Juju](https://juju.is/) [charm](https://juju.is/docs/olm/charmed-operators) deploying
and managing service for caching content, built on top of [Nginx](https://www.nginx.com/),
configurable to cache any HTTP or HTTPS web site and useful for building content delivery
networks (CDN).

This charm simplifies initial deployment and caching operations on Kubernetes, such as
scaling the number of cache instances and cache configuration changes. It allows for
deployment on many different Kubernetes platforms, from [MicroK8s](https://microk8s.io) to
[Charmed Kubernetes](https://ubuntu.com/kubernetes) and public cloud Kubernetes offerings.

This service was developed to provide front-end caching for web sites run by Canonical's
IS team, and to reduce the need for third-party CDNs by providing high-bandwidth access to
web sites via this caching front-end.

Currently used for a number of services including [the Snap Store](https://snapcraft.io/store),
the majority of Canonical's web properties including [ubuntu.com](https://ubuntu.com) and
[canonical.com](https://canonical.com), and [Ubuntu Extended Security Maintenance](https://ubuntu.com/security/esm).

For DevOps or SRE teams this charm will make operating it simple and straightforward through Juju's clean interface.

## In this documentation

| | |
|--|--|
|  [Tutorials](https://charmhub.io/content-cache-k8s/docs/tutorial-getting-started)</br>  Get started - a hands-on introduction to using the charm for new users </br> |  [How-to guides](https://charmhub.io/content-cache-k8s/docs/how-to-cache-content-with-openstack-swift) </br> Step-by-step guides covering key operations and common tasks |
| [Reference](https://charmhub.io/content-cache-k8s/docs/reference-actions) </br> Technical information - specifications, APIs, architecture | [Explanation](https://charmhub.io/content-cache-k8s/docs/explanation-charm-architecture) </br> Concepts - discussion and clarification of key topics  |

## Contributing to this documentation

Documentation is an important part of this project, and we take the same open-source approach
to the documentation as the code. As such, we welcome community contributions, suggestions,
and constructive feedback on our documentation. See
[How to contribute](https://charmhub.io/content-cache-k8s/docs/how-to-contribute) for more information.

If there’s a particular area of documentation that you’d like to see that’s missing,
please [file a bug](https://github.com/canonical/content-cache-k8s-operator/issues).

## Project and community

The content-cache-k8s charm is a member of the Ubuntu family. It's an open-source project that
warmly welcomes community  projects, contributions, suggestions, fixes, and constructive feedback.

- [Code of conduct](https://ubuntu.com/community/code-of-conduct)
- [Get support](https://discourse.charmhub.io/)
- [Join our online chat](https://matrix.to/#/#charmhub-charmdev:ubuntu.com)
- [Contribute](https://github.com/canonical/content-cache-k8s-operator/blob/main/CONTRIBUTING.md)

# Contents

1. [Tutorial](tutorial)
  1. [Basic deployment of the content-cache-k8s charm](tutorial/getting-started.md)
1. [How To](how-to)
  1. [Cache content with OpenStack/Swift storage](how-to/cache-content-with-openstack-swift.md)
  1. [How to contribute](how-to/contribute.md)
1. [Reference](reference)
  1. [Actions](reference/actions.md)
  1. [Configurations](reference/configurations.md)
  1. [External access](reference/external-access.md)
  1. [Relation endpoints](reference/integrations.md)
  1. [Redeployment](reference/charm-redeployment.md)
1. [Explanation](explanation)
  1. [Charm architecture](explanation/charm-architecture.md)