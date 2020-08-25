#!/bin/bash

# set environment variables for testing
export TEST=True
export AWS_STORAGE_BUCKET_NAME=nstpc-test
export AWS_STORAGE_BUCKET_NAME=nstpc-test
export AWS_SQS_DELETE_QUEUE_NAME=nstpc-delete-test
export AWS_SQS_TRANSFER_QUEUE_NAME=nstpc-transfer-test


python manage.py test $1