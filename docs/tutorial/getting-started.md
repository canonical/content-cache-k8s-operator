# Basic deployment of the content-cache-k8s charm

Deploy and integrate the Content-cache-k8s charm using Juju.

## What you’ll do

- Deploy the [Content-cache-k8s charm](https://charmhub.io/content-cache-k8s).
- Relate to [the Hello-kubecon charm](https://charmhub.io/hello-kubecon).
- Relate to [Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/#what-is-ingress) by using [NGINX Ingress Integrator](https://charmhub.io/nginx-ingress-integrator/).

Through the process, you'll inspect the Kubernetes resources created, verify the workload state and assign the Content-cache-k8s to serve your Hello-kubecon instance.

## What you'll need


- `Juju 3` installed.
- Juju controller and model created.
- NGINX Ingress Controller. If you're using [MicroK8s](https://microk8s.io/), this can be done by running the command `microk8s enable ingress`. For more details, see [Add-on: Ingress](https://microk8s.io/docs/addon-ingress).

For more information about how to install Juju, see [Get started with Juju](https://juju.is/docs/olm/get-started-with-juju).

### Deploy the content-cache-k8s charm

Since Content-cache is meant to serve as cache for another charm, we'll use Hello-kubecon as an example.

Deploy the charms:

```bash
juju deploy content-cache-k8s
juju deploy hello-kubecon
```

Run [`juju status`](https://juju.is/docs/olm/juju-status) to see the current status of the deployment. In the Unit list, you can see that Content-cache-k8s is blocked:

```bash
content-cache-k8s/0*  blocked   idle   10.1.97.227         Required config(s) empty: backend, site
hello-kubecon/0*      active    idle   10.1.97.193   
```

This is because the Content-cache-k8s charm isn't integrated with Hello-kubecon yet.

### Relate to the hello-kubecon charm

Provide integration between Content-cache-k8s and Hello-kubecon by running the following [`juju relate`](https://juju.is/docs/olm/juju-relate) command:

```bash
juju relate content-cache-k8s:nginx-proxy hello-kubecon
```

Run `juju status` to see that the message has changed:

```bash
content-cache-k8s/0*  active    idle   10.1.97.227         Ready
hello-kubecon/0*      active    idle   10.1.97.193
```

Note: `nginx-proxy` is the name of the relation. You can run `juju info content-cache-k8s` to check what are the relation names provided by the Content-cache-k8s application and `juju status --relations` to see the relations currently established in the model.

The deployment finishes when the status shows "Active".

### Relate to ingress by using NGINX ingress integrator

The NGINX Ingress Integrator charm can deploy and manage external access to HTTP/HTTPS services in a Kubernetes cluster.

If you want to make Content-cache-k8s charm available to external clients, you need to deploy the NGINX Ingress Integrator charm and integrate Content-cache-k8s with it.

See more details in [What is Ingress?](https://charmhub.io/nginx-ingress-integrator/docs/what-is-ingress).

Deploy the charm NGINX Ingress Integrator:

```bash
juju deploy nginx-ingress-integrator
```

If your cluster has [RBAC](https://kubernetes.io/docs/reference/access-authn-authz/rbac/) enabled, you'll be prompted to run the following:

```bash
juju trust nginx-ingress-integrator --scope cluster
```

Run `juju status` to verify the deployment.

Provide integration between Content-cache-k8s and NGINX Ingress Integrator:

```bash
juju relate content-cache-k8s nginx-ingress-integrator
```

Run `juju status` to see the same Ingress IP in the `nginx-ingress-integrator` message:

```bash
nginx-ingress-integrator                                active      1  nginx-ingress-integrator  stable    45  10.152.183.233  no       Ingress IP(s): 127.0.0.1, Service IP(s): 10.152.183.66
```

The default hostname for the Hello-kubecon application is `hello-kubecon`. To be able to browse to this site, that hostname will need to resolve to the IP address of your Ingress. You can achieve this by editing [`/etc/hosts`](https://manpages.ubuntu.com/manpages/kinetic/man5/hosts.5.html) file and adding the following line:

```bash
127.0.0.1 hello-kubecon
```

After that, visit `http://hello-kubecon` in a browser and you'll be presented with the home screen of the Hello-kubecon application.