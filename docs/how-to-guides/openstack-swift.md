Sometimes it is desirable to cache swift storage objects inside the charm for faster processing and reducing the number of requests to the swift server.

This guide will demonstrate how to deploy this charm along with Openstack swift storage.

First, connect to your openstack instance with your credentials, sourcing an .rc file:
```
source myfile.rc
```
Then list all the objects on the openstack containers in debug mode:
```
openstack object list default -vv
```
You will see a debug log as output. The URL should be located in the URL section of a curl command. The swift URL will look like this:
```
http://10.126.72.107:8080/v1/AUTH_fa8326b9fd4f405fb1c5eaafe988f5fd/default
```
After obtaining the URL, configure the charm to use that url as backend and site. Assuming the charm has been deployed as content-cache-k8s, run:
```
juju config content-cache-k8s backend="http://<swift_conn_url>:80"
juju config content-cache-k8s site="<swift_conn_url>"
```
Once configured, you can use swift commands to push or download objects. More details about swift commands [here](https://docs.openstack.org/ocata/cli-reference/swift.html)