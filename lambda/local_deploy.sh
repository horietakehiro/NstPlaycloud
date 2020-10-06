#!/bin/bash
export AWS_PAGER=""

# receive endpoint url as command line argumernt
if [ $# -eq 0 ];
then
    echo "specify endpoint url"
    exit
fi
ENDPOINT=$1

# create lambda packages
declare -a LambdaList=(
    # "image-util-layer"
    "thumbnail-creation"
    "image-deletion"
    "masking-creation"
)
mkdir -p ./artifacts
for lambda in ${LambdaList[@]}
do
    echo ">>>>> create artifacts of : ${lambda}"
    # skipp if artifact has already been built
    if [ -f ./artifacts/${lambda}/template.yaml ]
    then
        echo "<<<<< skipp creating artifact : ${lambda}"
        continue
    fi
    # replace requirements files,
    # because lambda layer is not available in standard Localstack
    cp ./src/${lambda}/${lambda//-/_}/requirements4localstack.txt \
        ./src/${lambda}/${lambda//-/_}/requirements.txt
    sam build   --use-container \
                --template ./src/${lambda}/template.yml \
                --build-dir ./artifacts/${lambda} \
                --debug
    # restore requirements file
    cp ./src/${lambda}/${lambda//-/_}/requirements4aws.txt \
        ./src/${lambda}/${lambda//-/_}/requirements.txt

    # create zip file and create lambda function
    cd `ls -d ./artifacts/${lambda}/*/` && \
        zip -r ${lambda}.zip . && \
        aws lambda create-function \
            --function-name ${lambda} \
            --runtime python3.6 \
            --zip-file fileb://${lambda}.zip \
            --handler app.lambda_handler \
            --role dummy \
            --region ap-northeast-1 \
            --environment Variables={S3_ENDPOINT=http://Localstack:4566/} \
            --endpoint-url ${ENDPOINT}
        rm -f ${lambda}.zip && \
        cd ../../../
    sleep 1
done

# # create and configure s3 buckets
BUCKET=nstpc
aws s3 mb s3://${BUCKET} --endpoint-url ${ENDPOINT}
aws s3api put-bucket-notification-configuration \
    --bucket ${BUCKET} \
    --notification-configuration file://config/s3-notification-configuration.json \
    --endpoint-url ${ENDPOINT}
# make the bucket public-accessible
aws s3api put-bucket-policy \
    --bucket ${BUCKET} \
    --policy file://config/s3-public-access-policy.json \
    --endpoint-url ${ENDPOINT}
aws s3api put-bucket-acl \
    --bucket ${BUCKET} \
    --acl public-read \
    --endpoint-url ${ENDPOINT}

# create sqs queues
# transfer queue
QUEUE=nstpc-transfer
aws sqs create-queue \
    --queue-name ${QUEUE} \
    --attributes MessageRetentionPeriod=43200,VisibilityTimeout=43200 \
    --endpoint-url ${ENDPOINT}
# delete queue
QUEUE=nstpc-delete
aws sqs create-queue \
    --queue-name ${QUEUE} \
    --attributes MessageRetentionPeriod=43200,VisibilityTimeout=43200 \
    --endpoint-url ${ENDPOINT}
# configure event mapping with delete-queue and image-deletion function
aws lambda create-event-source-mapping \
    --function-name image-deletion \
    --batch-size 10 \
    --event-source-arn arn:aws:sqs:ap-northeast-1:000000000000:${QUEUE} \
    --endpoint-url ${ENDPOINT}


# # create apigateway resource and map with the masking-creation function
# in advance, cleanup all rest-apis
REST_API_IDs=`aws apigateway get-rest-apis \
                --region ap-northeast-1 \
                --endpoint-url ${ENDPOINT} | jq -r .items[].id`
echo ">>>>> delete all existing apis : ${REST_API_IDs}"
for rest_api_id in ${REST_API_IDs}
do
    echo ">>>>> deleting rest-api : ${rest_api_id}"
    aws apigateway delete-rest-api \
        --rest-api-id ${rest_api_id} \
        --endpoint-url ${ENDPOINT}
done

echo ">>>>> create rest-api"
REST_API_ID=`aws apigateway create-rest-api \
                --name  nstpc-stack \
                --region ap-northeast-1 \
                --endpoint-url ${ENDPOINT} | jq -r .id`
echo "<<<<< rest-api-id : ${REST_API_ID}"
echo ">>>>> create resource"
PARENT_ID=`aws apigateway get-resources \
                --rest-api-id ${REST_API_ID} \
                --region ap-northeast-1 \
                --endpoint-url ${ENDPOINT} | jq -r .items[].id`
RESOURCE_ID=`aws apigateway create-resource \
                --rest-api-id ${REST_API_ID} \
                --region ap-northeast-1 \
                --parent-id ${PARENT_ID} \
                --path-part masking \
                --endpoint-url ${ENDPOINT} | jq -r .id`
echo "<<<<< resource-id : ${RESOURCE_ID}"
echo ">>>>> create method on rest-api"
aws apigateway put-method \
    --rest-api-id ${REST_API_ID} \
    --region ap-northeast-1 \
    --resource-id ${RESOURCE_ID} \
    --http-method POST \
    --authorization-type NONE \
    --endpoint-url ${ENDPOINT}

echo ">>>>> put integration with lambda"
aws apigateway put-integration \
    --region ap-northeast-1 \
    --rest-api-id ${REST_API_ID} \
    --resource-id ${RESOURCE_ID} \
    --http-method POST \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri arn:aws:apigateway:ap-northeast-1:lambda:path/2015-03-31/functions/arn:aws:lambda:ap-northeast-1:000000000000:function:masking-creation/invocations \
    --endpoint-url ${ENDPOINT}
echo ">>>>> deplaoyment rest-api"
aws apigateway create-deployment \
    --rest-api-id ${REST_API_ID} \
    --stage-name test \
    --endpoint-url ${ENDPOINT}
