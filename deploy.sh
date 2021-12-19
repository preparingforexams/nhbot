#!/bin/bash

set -e

v=$1
image=docker.io/torbencarstens/nhbot
k8sfile=.kubernetes/manifest.yaml

if [ -z $v ]; then
  echo 'you must provide a tag as an argument' 1>&2
  exit 1
fi

podman build -t $image:$v .
podman push $image:$v
sed -i -e "s/{{tag}}/${v}/g" $k8sfile
kubectl apply -f $k8sfile
sed -i -e "s/${v}/{{tag}}/g" $k8sfile
