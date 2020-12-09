# charm-k8s-content-cache

## Description

Deploy content caching layer into K8s.

## Usage

To deploy this charm into a k8s model:

    juju deploy cs:~content-cache-charmers/content-cache-k8s --config site=mysite.local --config backend=http://mybackend.local:80

And then you can test the deployment with:

    curl --resolve mysite.local:80:<ingress IP> http://mysite.local

### Scale Out Usage

Just run `juju scale-application <application name> 3`.

## Using a Custom Image

Build the docker image:

    git clone https://git.launchpad.net/charm-k8s-content-cache
    cd charm-k8s-content-cache/docker
    docker build . -t myimage:v<revision>
    docker tag myimage:v<revision> localhost:32000/myimage:v<revision>
    docker push localhost:32000/myimage:v<revision>

Then, to use your new image, either replace the `deploy` step above with

    juju deploy cs:~content-cache-charmers/content-cache-k8s --config image_path=localhost:32000/myimage:v<revision> --config site=mysite.local --config backend=http://mybackend.local:80

Or, if you have already deployed content-cache:

    juju config content-cache image_path=localhost:32000/myimage:v<revision>

## Developing

To build the charm locally, just run `charmcraft build`. You can then deploy
using:

    juju deploy ./content-cache.charm

To run lint against the code, run `make lint`.

## Testing

Just run `make unittest`.
