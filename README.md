# Content Cache Operator

A Juju charm deploying and managing a content cache.

## Overview

The content-cache service was developed to provide front-end caching for
services run by Canonical's IS team, and to reduce the need for third-party
CDNs to provide high-bandwidth access to those services. It's currently used
in production for a number of services including [the Snapstore](https://snapcraft.io/store),
the majority of Canonical's web properties including [ubuntu.com](https://ubuntu.com) and
[canonical.com](https://canonical.com), and [Ubuntu Extended Security Maintenance](https://ubuntu.com/security/esm).

This Kubernetes-based version is built using that same approach, and can be
used as a front-end caching service in a situation where your Kubernetes
cluster and its ingress controllers have a fast connection to the Internet.

## Usage

For details on using Kubernetes with Juju [see here](https://juju.is/docs/kubernetes), and for
details on using Juju with MicroK8s for easy local testing [see here](https://juju.is/docs/microk8s-cloud).

To deploy this charm into a k8s model, with sample configuration set up to
cache `archive.ubuntu.com`:

    juju deploy cs:~content-cache-charmers/content-cache-k8s --config site=archive.ubuntu.com --config backend=http://archive.ubuntu.com:80

And then you can test the deployment with:

    # Set this as appropriate
    UNIT_IP=10.1.234.11

First let's request a resource with headers telling us not to cache (with
sample output):

    curl -v --resolve archive.ubuntu.com:80:${UNIT_IP} http://archive.ubuntu.com/ubuntu/dists/focal/Release -o /dev/null 2>&1 | grep 'X-Cache-Status'
    # < X-Cache-Status: MISS from juju-87625f-hloeung-13 (content-cache-56bbcd79d6-h8dk2)
    curl -v --resolve archive.ubuntu.com:80:${UNIT_IP} http://archive.ubuntu.com/ubuntu/dists/focal/Release -o /dev/null 2>&1 | grep 'X-Cache-Status'
    # < X-Cache-Status: MISS from juju-87625f-hloeung-13 (content-cache-56bbcd79d6-h8dk2)

And now let's request a resource with headers that will allow us to cache:

    curl -v --resolve archive.ubuntu.com:80:${UNIT_IP} http://archive.ubuntu.com/ubuntu/dists/focal/Contents-i386.gz -o /dev/null 2>&1 | grep 'X-Cache-Status'
    # < X-Cache-Status: MISS from juju-87625f-hloeung-13 (content-cache-56bbcd79d6-h8dk2)
    curl -v --resolve archive.ubuntu.com:80:${UNIT_IP} http://archive.ubuntu.com/ubuntu/dists/focal/Contents-i386.gz -o /dev/null 2>&1 | grep 'X-Cache-Status'
    # < X-Cache-Status: HIT from juju-87625f-hloeung-13 (content-cache-56bbcd79d6-h8dk2)

---

For more details, [see here](https://charmhub.io/content-cache)
