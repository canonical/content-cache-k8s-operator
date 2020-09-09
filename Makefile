# Copyright (C) 2020 Canonical Ltd.
# See LICENSE file for licensing details.

lint:
	@echo "Normalising python layout with black."
	@tox -e black
	@echo "Running flake8"
	@tox -e lint

# We actually use the build directory created by charmcraft,
# but the .charm file makes a much more convenient sentinel.
unittest: content-cache.charm
	@tox -e unit

test: lint unittest

clean:
	@echo "Cleaning files"
	@git clean -fXd

content-cache.charm: src/*.py requirements.txt
	charmcraft build

.PHONY: lint test unittest clean
