# Cache content with openstack/swift storage

Sometimes it is desirable to cache swift storage objects inside the charm for faster processing and reducing the number of requests to the [swift](https://docs.openstack.org/swift/latest/) server. This also allows you to have a different hostname than the one from the Swift service.

This guide will demonstrate how to deploy this charm along with OpenStack/Swift storage.

First, connect to your openstack instance with your credentials, sourcing an .rc file:
```
source myfile.rc
```
if you don't have any credentials check [here](https://docs.openstack.org/zh_CN/user-guide/common/cli-set-environment-variables-using-openstack-rc.html) for more information.
The openstack container you are going to work with has to be globally readable. check that property:
```
swift stat <container_name>
```
And if it's not globally readable yet, change that with:
```
swift post <container_name> --read-acl ".r:*"
```
Then list all the objects on the openstack container in debug mode and get the url of the swift connection:
```
openstack object list <container_name> -vv 2>&1 | grep "^REQ: curl" | grep AUTH | cut -d'"' -f2 | cut -d'?' -f1
```
After obtaining the URL, configure the charm to use that url as our charm's backend. Assuming the charm has been deployed as content-cache-k8s, run:
```
juju config content-cache-k8s backend="http://<swift_conn_url>"
```
Once configured, you can use swift commands to push or download objects. More details about swift commands [here](https://docs.openstack.org/ocata/cli-reference/swift.html)

You can check everything is working by executing
```
curl <swift_conn_url>
```
And also add a relation to the nginx-ingress-integrator charm:
```
juju deploy nginx-ingress-integrator
```
If your cluster has [RBAC](https://kubernetes.io/docs/reference/access-authn-authz/rbac/) enabled, you'll be prompted to run the following:
```
juju trust nginx-ingress-integrator --scope cluster
```
The deployed application name will need to resolve to the IP of your ingress controller. A great way of testing this is to upload an index.html file into the openstack container and confirm that that content is reachable when they browse to this URL now.