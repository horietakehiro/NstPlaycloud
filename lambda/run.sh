#!/bin/bash

docker run \
    -itd \
    --name aws-sam \
    --hostname aws-sam \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v ${PWD}/src:/var/opt \
    -e S3_ENDPOINT=http://docker.for.mac.localhost:4566 \
    -e PYTHONPATH=/var/opt/image-deletion/image_deletion \
    aws-sam:python36
