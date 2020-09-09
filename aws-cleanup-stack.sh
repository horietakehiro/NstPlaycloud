#!/bin/bash

# cleanup s3 buckets
declare -a BucketList=(
    "nstpc"
    "nstpc-artifacts"
)

for bucket in ${BucketList[@]}
do
    echo ">>>>> cleanup bucket : ${bucket}"
    aws s3 rb s3://${bucket} --force 2>/dev/null
done

echo ">>>>> delete stack : nstpc-stack"
aws cloudformation delete-stack --stack-name nstpc-stack
echo ">>>>> wait until the deletion gets completed."
aws cloudformation wait stack-delete-complete --stack-name nstpc-stack
echo "<<<<< stack deletion has completed"