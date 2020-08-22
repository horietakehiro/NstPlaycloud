#!/bin/bash

# set environment variables for testing
export TEST=True
export AWS_STORAGE_BUCKET_NAME=nstpc-test
export AWS_STORAGE_BUCKET_NAME=nstpc-test
export AWS_SQS_QUEUE_NAME=nstpc-test



python manage.py test $1