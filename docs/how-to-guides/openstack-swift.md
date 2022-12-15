Sometimes it is desirable to cache swift storage objects inside the charm for faster processing and reducing the number of requests to the [swift](https://docs.openstack.org/swift/latest/) server.

This guide will demonstrate how to deploy this charm along with OpenStack/Swift storage.

First, connect to your openstack instance with your credentials, sourcing an .rc file:
```
source myfile.rc
```
if you don't have any credentials check [here](https://docs.openstack.org/zh_CN/user-guide/common/cli-set-environment-variables-using-openstack-rc.html) for more information
Then list all the objects on the openstack containers in debug mode:
```
openstack object list default -vv
```
You will see a debug log as output. The URL should be located in the URL section of a `curl` command. The swift URL will look like this:
```
http://10.126.72.107:8080/v1/AUTH_fa8326b9fd4f405fb1c5eaafe988f5fd/default
```
Or directly filter the url from the debug log instead of searching into the output:
```
openstack object list default -vv 2>&1 | grep "^REQ: curl" | grep AUTH | cut -d'"' -f2 | cut -d'?' -f1
```
After obtaining the URL, configure the charm to use that url as backend and site. Assuming the charm has been deployed as content-cache-k8s, run:
```
juju config content-cache-k8s backend="http://<swift_conn_url>:80"
juju config content-cache-k8s site="<swift_conn_url>"
```
Once configured, you can use swift commands to push or download objects. More details about swift commands [here](https://docs.openstack.org/ocata/cli-reference/swift.html)

You can check everything is working by executing
```
curl <swift_conn_url>
```