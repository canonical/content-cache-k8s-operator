---
myst:
  html_meta:
    "description lang=en": "Discover the Content Cache K8s charm, a Juju operator that deploys and manages an NGINX content cache on Kubernetes."
---

(index)=

# Content Cache K8s charm

A [Juju](https://canonical.com/juju) {ref}`charm <juju:charm>` deploying and managing a static
web content cache with [NGINX](https://www.nginx.com/) on Kubernetes. Use it to cache
any HTTP or HTTPS web site, and to build a content delivery network (CDN).

The charm runs NGINX as a caching reverse proxy in front of a web site. When a client
sends a request, the cache returns a saved copy of the response if it has one and the copy
is still valid. Otherwise, the cache fetches the response from the backend, stores it, and
passes it to the client. This lowers the load on the origin web site and shortens response
times for repeated requests.

Like any Juju charm, this charm supports one-line deployment, configuration, integration,
scaling, and more. For Content Cache K8s, this includes:

- Caching any HTTP or HTTPS web site, with tuning for the cache size, the cached response
  codes, and the lifetime of cached content.
- Scaling the number of cache instances to match your traffic.
- Serving as the cache for another charmed application that uses the `nginx-proxy` relation,
  or caching a web site that you configure directly with the `site` and `backend` options.
- Observability through the Canonical Observability Stack, with a Grafana dashboard,
  Prometheus metrics, and Loki logs.
- Deployment on many different Kubernetes platforms, from
  [Canonical Kubernetes](https://documentation.ubuntu.com/canonical-kubernetes/latest/)
  to public cloud Kubernetes offerings.

This service was developed to provide front-end caching for web sites run by Canonical's
IS team, and to reduce the need for third-party CDNs by providing high-bandwidth access to
web sites via this caching front-end. It is currently used for services including
[the Snap Store](https://snapcraft.io/store), most of Canonical's web properties such as
[ubuntu.com](https://ubuntu.com) and [canonical.com](https://canonical.com), and
[Ubuntu Extended Security Maintenance](https://ubuntu.com/security/esm).

This charm will make operating a content cache straightforward for DevOps and SRE teams
through Juju's clean interface.

## In this documentation

```{list-table}
   :header-rows: 0
   :widths: 20 80

* - **Get started**
  - {ref}`Deploy the charm <tutorial_getting_started>`
* - **Deployment**
  - {ref}`Configurations <reference_configurations>` | {ref}`External access <reference_external_access>`
* - **Integrations**
  - {ref}`Relation endpoints <reference_integrations>`
* - **Operations**
  - {ref}`Cache content from OpenStack Swift <how_to_cache_content_with_openstack_swift>` | {ref}`Upgrade <how_to_upgrade>` | {ref}`Redeployment <reference_charm_redeployment>` | {ref}`Actions <reference_actions>`
* - **Design**
  - {ref}`Charm architecture <reference_charm_architecture>`
* - **Security**
  - {ref}`Security overview <explanation_security>`
```

## How this documentation is organized

This documentation uses the [Diátaxis documentation structure](https://diataxis.fr/).

- The {ref}`Tutorial <tutorial_index>` takes you step-by-step through a basic deployment of the Content Cache K8s charm, and how to integrate it with a backend application.
- {ref}`How-to guides <how_to_index>` assume basic familiarity with the charm. They cover key operations and common tasks, such as caching content from an OpenStack Swift container, upgrading the charm, and contributing to the project.
- {ref}`Reference <reference_index>` provides technical details on actions, configurations, relation endpoints, and the charm architecture.
- {ref}`Explanation <explanation_index>` includes topic overviews, background, and context, such as the security design of the charm.
- The {ref}`Changelog <changelog>` lists user-relevant changes for each revision of the charm.

### Contributing to this documentation

Documentation is an important part of this project, and we take the same open-source approach
to the documentation as the code. As such, we welcome community contributions, suggestions,
and constructive feedback on our documentation. Read {ref}`How to contribute <how_to_contribute>`
to learn how to report a problem or propose a change.

If there's a particular area of documentation that you'd like to see that's missing,
please [file a bug](https://github.com/canonical/content-cache-k8s-operator/issues), or open a
pull request with your change.

## Project and community

The Content Cache K8s charm is a member of the Ubuntu family. It's an open-source project that
warmly welcomes community projects, contributions, suggestions, fixes, and constructive feedback.

### Governance and policies

- [Code of conduct](https://ubuntu.com/community/code-of-conduct)

### Get involved

- [File a bug](https://github.com/canonical/content-cache-k8s-operator/issues)
- Get support through the [Discourse forum](https://discourse.charmhub.io/)
- Join our [online chat](https://matrix.to/#/#charmhub-charmdev:ubuntu.com)
- {ref}`Contribute <how_to_contribute>`

### Releases

- {ref}`Changelog <changelog>`

Thinking about using the Content Cache K8s charm for your next project?
[Get in touch](https://matrix.to/#/#charmhub-charmdev:ubuntu.com)!

```{toctree}
:hidden:
:maxdepth: 1

Tutorial <tutorial/index>
How-to guides <how-to/index>
Reference <reference/index>
Explanation <explanation/index>
Changelog <CHANGELOG>
```
