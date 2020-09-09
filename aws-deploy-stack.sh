#!/bin/bash

# creaet artifacts of lambda to artifacts/
declare -a LambdaList=(
    "image-util-layer"
    "thumbnail-creation"
    "image-deletion"
    "masking-creation"
)
mkdir -p artifacts
for lambda in ${LambdaList[@]}
do
    echo ">>>>> create artifacts of : ${lambda}"
    # skipp if artifact has already been built
    ls ./artifacts/${lambda}/template.yaml &>/dev/null
    if test $? -eq 0
    then
        echo "<<<<< skipp creating artifact : ${lambda}"
        continue
    fi

    sam build   --use-container \
                --template ./lambda/src/${lambda}/template.yml \
                --build-dir artifacts/${lambda}
    sleep 1
done

# packagin artifacts
# check if the bucket for artifact already exists. If not exists, create in advance
BUCKET=nstpc-artifacts
echo ">>>>> cleanup bucket for artifact : ${BUCKET}"
aws s3 rb s3://${BUCKET} --force &> /dev/null
echo ">>>>> creating bucket for artifact : ${BUCKET}"
aws s3 mb s3://${BUCKET}
echo ">>>>> uploading artifacts to bucket : ${BUCKET}"
aws cloudformation package  --template cloudformation-raw.yml \
                            --s3-bucket ${BUCKET} \
                            --output-template-file cloudformation-packaged.yml
# use ONEZONE_IA storage class as bucket for artifacts
aws s3 cp s3://${BUCKET} s3://${BUCKET} --recursi --storage-class ONEZONE_IA


# deploy main
echo ">>>>> deploying nstpc-stack"
# aws cloudformation deploy   --stack-name nstpc-stack \
#                             --template-file cloudformation-packaged.yml \
#                             --capabilities CAPABILITY_IAM
sam deploy  --stack-name nstpc-stack \
            --template-file cloudformation-packaged.yml \
            --capabilities CAPABILITY_IAM