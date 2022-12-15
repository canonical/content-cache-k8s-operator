# Swift Storage How-To

In order to use this charm along with Openstack swift storage you'll need to do the following:

First, connect to your openstack instance with your credentials, normally sourcing an .rc file:
```
source myfile.rc
```
Then execute:
```
openstack object list default -vv
```
and you will see a debug log. THe URL should be located in the URL section of a curl command or similar. The swift URL looks like this:
```
http://10.126.72.107:8080/v1/AUTH_fa8326b9fd4f405fb1c5eaafe988f5fd/default
```
After obtaining the URL, configure the charm to use that url as backend and site:
```
juju config content-cache-k8s backend="http://<swift_conn_url>:80"
juju config content-cache-k8s site="<swift_conn_url>"
```
And then use swift commands to push or download objects. More details about swift commands [here](https://docs.openstack.org/ocata/cli-reference/swift.html)