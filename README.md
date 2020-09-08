# charm-k8s-content-cache

## Description

Deploy content caching layer into K8s.

## Usage

Build the docker image:

    `cd docker`
    `docker build . -t myimage:v<revision>`
    `docker tag myimage:v<revision> localhost:32000/myimage:v<revision>`
    `docker push localhost:32000/myimage:v<revision>`

Deploy:

    `juju deploy content-cache.charm --config image_path=localhost:32000/myimage:v<revision> --config site=mysite.local --config backend=http://mybackend.local:80`

### Test Deployment

`curl --resolve mysite.local:80:<ingress IP> http://mysite.local`

### Scale Out Usage

Just run `juju add-unit <application name>`.

## Developing

Just run `make lint`.

## Testing

Just run `make unittest`.
