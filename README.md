# Content Cache Operator

A Juju charm for deploying and managing a content cache.

## Overview

A service for caching content, built on top of [Nginx](https://www.nginx.com/),
configurable to cache any http or https web site. Tuning options include
cache storage size, maximum request size to cache and cache validity duration.

This service was developed to provide front-end caching for web sites run by
Canonical's IS team, and to reduce the need for third-party CDNs by providing
high-bandwidth access to web sites via this caching front-end. Currently used
for a number of services including [the Snap Store](https://snapcraft.io/store),
the majority of Canonical's web properties including [ubuntu.com](https://ubuntu.com) and
[canonical.com](https://canonical.com), and [Ubuntu Extended Security Maintenance](https://ubuntu.com/security/esm).

This Kubernetes-based version is built using the same approach as the [machine content-cache charm](https://charmhub.io/content-cache), and can be used as a front-end caching service in
a situation where your Kubernetes cluster and its ingress controllers have
a fast connection to the Internet.

## Project and community

The Content-cache-k8s Operator is a member of the Ubuntu family. It's an
open source project that warmly welcomes community projects, contributions,
suggestions, fixes and constructive feedback.
* [Code of conduct](https://ubuntu.com/community/code-of-conduct)
* [Get support](https://discourse.charmhub.io/)
* [Join our online chat](https://chat.charmhub.io/charmhub/channels/charm-dev)
* [Contribute](https://charmhub.io/content-cache-k8s/docs/contributing)
Thinking about using the Content-cache-k8s for your next project? [Get in touch](https://chat.charmhub.io/charmhub/channels/charm-dev)!

---

For further details, [see here](https://charmhub.io/content-cache-k8s/docs)