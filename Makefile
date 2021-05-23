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
unittest: content-cache-k8s.charm
	@tox -e unit

test: lint unittest

clean:
	@echo "Cleaning files"
	@git clean -fXd

content-cache-k8s.charm: lib/charms/*/v*/*.py src/*.py requirements.txt
	charmcraft build

.PHONY: lint test unittest clean
