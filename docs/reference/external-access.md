# External access

The only external access required by this charm is if it's configured to
connect to an external backend, using the `backend` configuration option. As
an example, if this is set to `http://mybackend.local:80`, then this charm
will need to be able to access that hostname on port 80 to be able to serve
content for it.
