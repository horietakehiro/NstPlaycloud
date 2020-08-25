#!/bin/bash

EP=http://localhost:4566/

# s3
aws s3 mb s3://nstpc --endpoint-url=${EP}
aws s3api put-bucket-notification-configuration \
    --bucket nstpc --notification-configuration file://s3-notification-configuration.json \
    --endpoint-url=${EP}

# sqs
aws sqs create-queue --queue-name nstpc-delete --endpoint-url=${EP}
aws sqs create-queue --queue-name nstpc-transfer --endpoint-url=${EP}
