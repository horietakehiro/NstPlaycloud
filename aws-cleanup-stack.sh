#!/bin/bash

# buckups images in bucket
mkdir -p ./backups/original
aws s3 cp s3://nstpc/media/original ./backups/original/ --recursive

# cleanup s3 buckets
declare -a BucketList=(
    "nstpc"
    "nstpc-artifacts"
    "elasticbeanstalk-nstpc-ap-northeast-1"
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

SIR=`aws ec2 describe-spot-instance-requests | jq -r .SpotInstanceRequests[].SpotInstanceRequestId`
echo ">>>>> cancel spot isntance request(s) : ${SIR}"
aws ec2 cancel-spot-instance-requests --spot-instance-request-ids ${SIR}
