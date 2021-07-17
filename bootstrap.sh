#!/bin/bash

set -o errexit
set -o nounset

IMAGE=jcasts:latest
POD=jcasts
CONFIG_DIR=k8s/local

podman build -t $IMAGE .

if podman pod exists $POD
then
    echo "stopping and removing pod $POD"
    podman pod stop $POD
    podman pod rm $POD
fi

podman play kube $CONFIG_DIR/pod.yml --configmap=$CONFIG_DIR/configMap.yml
