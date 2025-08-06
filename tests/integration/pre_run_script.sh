#!/bin/bash

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

# Pre-run script for integration test operator-workflows action.
# https://github.com/canonical/operator-workflows/blob/main/.github/workflows/integration_test.yaml

# Workaround for a bug in Calico and/or MicroK8s which results in doubled
# iptables entries to redirect traffic to k8s pods.
#
# Affected rule looks like:
# num  target     prot opt source               destination
#1    CNI-DN-6832ce82caf043689e15f  tcp  --  anywhere             anywhere             /* dnat name: "k8s-pod-network" id: "9b452011f0c5049380e9bc4ea23014fb984b8f8e20415f8f9e0c8e1ce5e26ac9" */ multiport dports http,https,10254
#2    CNI-DN-6832ce82caf043689e15f  tcp  --  anywhere             anywhere             /* dnat name: "k8s-pod-network" id: "9b452011f0c5049380e9bc4ea23014fb984b8f8e20415f8f9e0c8e1ce5e26ac9" */ multiport dports http,https,10254

echo "Checking iptables: there should be only one rule"
sudo iptables-legacy -t nat -L CNI-HOSTPORT-DNAT

echo "Trying to remove extra entry"
sudo iptables-legacy -t nat -D CNI-HOSTPORT-DNAT 2 || echo "No extra entry"
