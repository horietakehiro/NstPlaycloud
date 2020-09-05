#!/bin/bash

# set environment variables for testing
export TEST=True
export AWS_STORAGE_BUCKET_NAME=test-nstpc

export AWS_SQS_DELETE_QUEUE_NAME=test-nstpc-delete
export AWS_SQS_TRANSFER_QUEUE_NAME=test-nstpc-transfer

export AWS_APIGW_RESTAPI_NAME=test-nstpc


python manage.py test $1