#!/bin/bash

if [ $# -eq 0 ];
then
    echo "specify lambda name"
    exit
fi
LAMBDA=$1


docker run \
    -itd \
    --name aws-sam \
    --hostname aws-sam \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v ${PWD}/src:/var/opt \
    -v ${PWD}/config/aws:/root/.aws \
    -e S3_ENDPOINT=http://docker.for.mac.localhost:4566 \
    -e PYTHONPATH=/var/opt/${LAMBDA}/${LAMBDA//-/_} \
    aws-sam:python36
