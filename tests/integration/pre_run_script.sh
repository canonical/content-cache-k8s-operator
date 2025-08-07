#!/bin/bash

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

# Pre-run script for integration test operator-workflows action.
# https://github.com/canonical/operator-workflows/blob/main/.github/workflows/integration_test.yaml

# Workaround for some bad interactions between devstack setup and microk8s setup

# When deploying devstack after microk8s some
# iptables entries to redirect traffic to k8s pods are duplicated.
#
# Affected rule looks like:
# num  target     prot opt source               destination
#1    CNI-DN-6832ce82caf043689e15f  tcp  --  anywhere             anywhere             /* dnat name: "k8s-pod-network" id: "9b452011f0c5049380e9bc4ea23014fb984b8f8e20415f8f9e0c8e1ce5e26ac9" */ multiport dports http,https,10254
#2    CNI-DN-f659e1bd219a5f3afd378  tcp  --  anywhere             anywhere             /* dnat name: "k8s-pod-network" id: "5b1508a92274579cd23b41ff8d9732583b39a2802395d397cafd5389a29c9359" */ multiport dports http,https,10254

echo "Checking iptables: there should be only one rule"
sudo iptables-legacy -t nat -L CNI-HOSTPORT-DNAT

DUP=$(sudo iptables-legacy -t nat -L CNI-HOSTPORT-DNAT 2)
if [ -n "$DUP" ]; then
	echo "Removing first rule"
	sudo iptables-legacy -t nat -D CNI-HOSTPORT-DNAT 1
fi
