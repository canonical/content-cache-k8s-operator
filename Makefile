# Copyright (C) 2020 Canonical Ltd.
# See LICENSE file for licensing details.

blacken:
	@echo "Normalising python layout with black."
	@tox -e black

lint: blacken
	@echo "Running flake8"
	@tox -e lint

# We actually use the build directory created by charmcraft,
# but the .charm file makes a much more convenient sentinel.
unittest: charm-fetch‐lib content-cache-k8s.charm
	@tox -e unit

test: lint unittest

clean:
	@echo "Cleaning files"
	@git clean -fXd

charm-fetch‐lib:
	# charmcraft fetch-lib charms.nginx_ingress_integrator.v0.ingress

content-cache-k8s.charm: src/*.py requirements.txt
	charmcraft build

build: clean charm-fetch‐lib
	charmcraft build

.PHONY: lint unittest test clean build charm-fetch‐lib
