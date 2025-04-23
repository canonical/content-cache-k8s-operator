# Security in Content Cache K8s charm

This document describes the security design of the Content Cache K8s charm. The charm manages a [nginx web server](https://nginx.org/) configured as a static web content cache. This document will detail the risks and good practices.

## Machine-in-the-middle attack

This type of attack refers to an attacker intercepting messages and pretend to be the intended recipient of the message.
For example, if an user tries to access `ubuntu.com`, an attacker might intercept the packets and pretend to be `ubuntu.com`, and trick the user to reveal their password.
The way to prevent this would be using TLS certificates to valid the identity of recipient.

The incoming traffic to the charm should be encrypted with SSL to ensure that attackers cannot impersonate domains cached by the charm.

### Good practices

Enable TLS certificates with the [`tls_secret_name` configuration](https://charmhub.io/content-cache-k8s/configurations#tls_secret_name).

## Caching of sensitive data

The Content Cache K8s charm caches the response of the host and reuse it for future requests.
If the response from the host contains sensitive data, then the response should not be stored and re-used for future requests.

For example, a response with `Set-Cookie` header is commonly used to store login session to the client browser. If this response is cached and re-used for future requests then other people might gain access to the login session of the original request.

When Nginx designed the content cache feature, this risk was considered. By default nginx does not cache response with `Set-Cookie` in the header.
The host can also control the caching behaviors with `Cache-Control`.
By default, Nginx respects  the `Cache-Control` header. If the header is set to value such as `private`, `no-cache`, `no-store`, Nginx would not cache the response.
The charm does not override this default setting.

### Good practice

Check if the hosts being cached are using the `Cache-Control` to prevent caching for sensitive responses.
