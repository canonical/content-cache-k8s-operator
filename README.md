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

To deploy this charm into a k8s model, with sample configuration set up to
cache `archive.ubuntu.com` on `archive.local`:

    juju deploy content-cache-k8s --channel edge \
        --config site=archive.local \
        --config backend=http://archive.ubuntu.com:80 \
        content-cache
    juju deploy nginx-ingress-integrator content-cache-ingress
    juju relate content-cache content-cache-ingress

And then you can test the deployment with:

    # Set this to to the "Ingress with service IP" value from the content-cache-ingress service from `juju status`
    APP_IP=10.152.183.117

First let's request a resource with headers that will allow us to cache (with
sample output):

    curl -v --resolve archive.local:80:${APP_IP} http://archive.local/ubuntu/dists/focal/Contents-i386.gz -o /dev/null 2>&1 | grep 'X-Cache-Status'
    # < X-Cache-Status: MISS from juju-87625f-hloeung-13 (content-cache-56bbcd79d6-h8dk2)
    #  First result is a cache MISS
    curl -v --resolve archive.local:80:${APP_IP} http://archive.local/ubuntu/dists/focal/Contents-i386.gz -o /dev/null 2>&1 | grep 'X-Cache-Status'
    # < X-Cache-Status: HIT from juju-87625f-hloeung-13 (content-cache-56bbcd79d6-h8dk2)
    #  Second result is a cache HIT

And now let's request a resource which has headers telling us not to cache:

    # Verify cache control headers on the upstream resource
    curl -v http://archive.ubuntu.com/ubuntu/dists/focal/Release 2>&1 | grep 'Cache-Control'
    #   output: < Cache-Control: max-age=0, proxy-revalidate
    # And now perform the requests through the content-caching service
    curl -v --resolve archive.local:80:${APP_IP} http://archive.local/ubuntu/dists/focal/Release -o /dev/null 2>&1 | grep 'X-Cache-Status'
    # < X-Cache-Status: MISS from juju-87625f-hloeung-13 (content-cache-56bbcd79d6-h8dk2)
    #  First result is a cache MISS
    curl -v --resolve archive.local:80:${APP_IP} http://archive.local/ubuntu/dists/focal/Release -o /dev/null 2>&1 | grep 'X-Cache-Status'
    # < X-Cache-Status: MISS from juju-87625f-hloeung-13 (content-cache-56bbcd79d6-h8dk2)
    #  Second result still a cache MISS

---

For more details, [see here](https://charmhub.io/content-cache-k8s/docs)
