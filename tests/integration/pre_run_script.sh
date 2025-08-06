#!/bin/bash

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

# Pre-run script for integration test operator-workflows action.
# https://github.com/canonical/operator-workflows/blob/main/.github/workflows/integration_test.yaml

#IPADDR=$(ip -4 -j route get 2.2.2.2 | jq -r '.[] | .prefsrc')
#sudo microk8s enable "metallb:$IPADDR-$IPADDR"
