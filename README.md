# Content Cache Operator

A Juju charm for deploying and managing a content cache.

## Overview

A service for caching content, built on top of [Nginx](https://www.nginx.com/)
configurable to cache any http or https web site. Tuning options include
cache storage size, maximum request size to cache and cache validity duration.

This service was developed to provide front-end caching for web sites run by
Canonical's IS team, and to reduce the need for third-party CDNs by providing
high-bandwidth access to web sites via this caching front-end. Currently used
for a number of services including [the Snap Store](https://snapcraft.io/store),
the majority of Canonical's web properties including [ubuntu.com](https://ubuntu.com) and
[canonical.com](https://canonical.com), and [Ubuntu Extended Security Maintenance](https://ubuntu.com/security/esm).

This Kubernetes-based version is built using the same approach, and can be
used as a front-end caching service in a situation where your Kubernetes
cluster and its ingress controllers have a fast connection to the Internet.

## Usage

For details on using Kubernetes with Juju [see here](https://juju.is/docs/kubernetes), and for
details on using Juju with MicroK8s for easy local testing [see here](https://juju.is/docs/microk8s-cloud).

To deploy this charm into a k8s model:

    juju deploy content-cache-k8s --channel edge
    juju deploy hello-kubecon
    juju deploy nginx-ingress-integrator
    juju relate hello-kubecon content-cache-k8s:ingress-proxy
    juju relate nginx-ingress-integrator content-cache-k8s:ingress

You can then reach the site at `http://hello-kubecon` assuming `hello-kubecon`
resolves to the IP address of your Kubernetes cluster (if you're on MicroK8s
this will be 127.0.0.1).

---

For more details, [see here](https://charmhub.io/content-cache-k8s/docs)
