# External access

This charm requires external access only if it's configured to
connect to an external backend using the
[`backend` configuration option](https://charmhub.io/content-cache-k8s/configurations#backend).
For example, if `backend` is set to `http://mybackend.local:80`, then this charm
will need to access `http://mybackend.local` on port 80 to be able to serve
content for it.