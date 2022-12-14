For any problems with this charm, please [report bugs here](https://github.com/canonical/content-cache-k8s-operator/issues).

The code for this charm can be downloaded as follows:

```
git clone https://github.com/canonical/content-cache-k8s-operator
```

To run tests, simply run  `make test`  from within the charm code directory.

## Using a Custom Image

Build the docker image:

    git clone https://github.com/canonical/content-cache-k8s-operator
    cd charm-k8s-content-cache/docker
    docker build . -t myimage:v<revision>
    docker tag myimage:v<revision> localhost:32000/myimage:v<revision>
    docker push localhost:32000/myimage:v<revision>

Then, to use your new image, either replace the `deploy` step above with

    juju deploy content-cache-k8s --config image_path=localhost:32000/myimage:v<revision> --config site=mysite.local --config backend=http://mybackend.local:80                                                                                                

Or, if you have already deployed content-cache:

    juju config content-cache image_path=localhost:32000/myimage:v<revision>

## Developing

To build the charm locally, just run `charmcraft build`. You can then deploy using:

    juju deploy ./content-cache.charm

To run lint against the code, run `make lint`.