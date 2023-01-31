# Quick Guide

## What you’ll learn

- Deploy the [Content-cache-k8s charm](https://charmhub.io/content-cache-k8s).
- Relate to [the Hello-Kubecon charm](https://charmhub.io/hello-kubecon).
- Relate to [Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/#what-is-ingress) by using [NGINX Ingress Integrator](https://charmhub.io/nginx-ingress-integrator/).

Through the process, you'll inspect the Kubernetes resources created, verify the workload state, and log in to your Indico instance.

## Requirements

- Juju 3 installed.
- Juju controller and model created.
- NGINX Ingress Controller. If you're using [MicroK8s](https://microk8s.io/), this can be done by running the command `microk8s enable ingress`. For more details, see [Addon: Ingress](https://microk8s.io/docs/addon-ingress).

For more information about how to install Juju, see [Get started with Juju](https://juju.is/docs/olm/get-started-with-juju).

### Deploy the Content-cache-k8s charm

Since Content-cache is meant to serve another charm as its cache, we'll use Hello-kubecon as an example.

Deploy the charms:

```bash
juju deploy content-cache-k8s
juju deploy hello-kubecon
```

To see the pod created by the Indico charm, run `kubectl get pods` on a namespace named for the Juju model you've deployed the Content-cache charm into. The output is similar to the following:

```bash
modeloperator-98b8cb7df-m6stx   1/1     Running   0          2m20s
content-cache-k8s-0             3/3     Running   0          2m
hello-kubecon-0                 0/2     Running   0          36s
```

Run [`juju status`](https://juju.is/docs/olm/juju-status) to see the current status of the deployment. In the Unit list, you can see that Indico is waiting:

```bash
content-cache-k8s/0*  blocked   idle   10.1.97.227         Required config(s) empty: backend, site
hello-kubecon/0*      active    idle   10.1.97.193   
```

This means that Content-cache-k8s charm isn't integrated with hello-kubecon yet.

### Relate to the Redis K8s charm the PostgreSQL K8s charm

Provide integration between Content-cache-k8s and Hello-kubecon by running the following [`juju relate`](https://juju.is/docs/olm/juju-relate) command:

```bash
juju relate content-cache-k8s:ingress-proxy hello-kubecon
```

Run `juju status` to see that the message has changed:

```bash
content-cache-k8s/0*  active    idle   10.1.97.227         Ready
hello-kubecon/0*      active    idle   10.1.97.193
```

Note: `ingress-proxy` is the name of the relation. This is needed because establishes that the two charms are compatible with each other.  You can run `juju info content-cache-k8s` to check what are the relation names provided by the Content-cache-k8s application.

The deployment finishes when the status shows "Active".

### Relate to Ingress by using NGINX Ingress Integrator

The NGINX Ingress Integrator charm can deploy and manage external access to HTTP/HTTPS services in a Kubernetes cluster.

If you want to make Content-cache-k8s charm available to external clients, you need to deploy the NGINX Ingress Integrator charm and integrate Content-cache-k8s with it.

See more details in [Adding the Ingress Relation to a Charm](https://charmhub.io/nginx-ingress-integrator/docs/adding-ingress-relation).

Deploy the charm NGINX Ingress Integrator:

```bash
juju deploy nginx-ingress-integrator
```

If your cluster has [RBAC](https://kubernetes.io/docs/reference/access-authn-authz/rbac/) enabled, you'll be prompted to run the following:

```bash
juju trust nginx-ingress-integrator --scope cluster
```

Run `juju status` to verify the deployment.

Provide integration between Indico and NGINX Ingress Integrator:

```bash
juju relate content-cache-k8s:ingress nginx-ingress-integrator

```

To see the Ingress resource created, run `kubectl get ingress` on a namespace named for the Juju model you've deployed the Content-cache-k8s charm into. The output is similar to the following:

```bash
NAME                    CLASS    HOSTS           ADDRESS     PORTS   AGE
hello-kubecon-ingress   public   hello-kubecon   127.0.0.1   80      2m11s
```

Run `juju status` to see the same Ingress IP in the `nginx-ingress-integrator` message:

```bash
nginx-ingress-integrator                                active      1  nginx-ingress-integrator  stable    45  10.152.183.233  no       Ingress IP(s): 127.0.0.1, Service IP(s): 10.152.183.66
```

The browser uses entries in the /etc/hosts file to override what is returned by a DNS server.

The default hostname for the Hello-kubecon application is `hello-kubecon`. To resolve it to your Ingress IP, edit [`/etc/hosts`](https://manpages.ubuntu.com/manpages/kinetic/man5/hosts.5.html) file and add the following line accordingly:

```bash
127.0.0.1 hello-kubecon
```

Optional: run `echo "127.0.0.1 hello-kubecon" >> /etc/hosts` to redirect the output of the command `echo` to the end of the file `/etc/hosts`.

After that, visit `http://hello-kubecon` in a browser and you'll be presented with a screen to create an initial admin account.
