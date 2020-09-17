#!/bin/bash


# check if secret parameters are set
if [ ! -f secrets ]
then
    echo "create the file : 'secrets' for secrets parameters"
    echo "required parameters are shown below"
    echo -e "\e[31m"
    cat secrets.org
    echo -e "\e[m"
    exit
fi
# confirm that secret parameters are valid
echo -e "\e[31m===== show secret parameters start ====="
cat secrets
echo "===== show secret parameters end   ====="
answer=""
while [[ ${answer} != [yn] ]]
do
    read -n1 -p "Secrets parameters above are certainly right? [y/n]:" answer; echo 
done
echo -e "\e[m"
if [ ${answer} = "n" ]
then
    echo "deployment cancelled"
    exit
fi

# export secret parameters
. secrets


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
    if [ -f ./artifacts/${lambda}/template.yaml ]
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
aws s3 cp s3://${BUCKET} s3://${BUCKET} --recursive --storage-class ONEZONE_IA


# create artifact for elastic beanstalk application
echo ">>>>> create artifacts of : frontend"
# create artifact for frontend
echo ">>>>> zip frontend src"
mkdir -p artifacts/frontend
cd frontend/src && zip -r frontend.zip . && mv frontend.zip ../../artifacts/frontend/ && cd ../../
# upload frontend's artifact to s3
BUCKET=elasticbeanstalk-nstpc-ap-northeast-1
echo ">>>>> cleanup bucket for artifact : ${BUCKET}"
aws s3 rb s3://${BUCKET} --force &> /dev/null
echo ">>>>> creating bucket for artifact : ${BUCKET}"
aws s3 mb s3://${BUCKET}
echo ">>>>> uploading artifacts to bucket : ${BUCKET}"
aws s3 cp artifacts/frontend/frontend.zip s3://${BUCKET} --storage-class ONEZONE_IA


# deploy main
echo ">>>>> deploying nstpc-stack"
sam deploy  --stack-name nstpc-stack \
            --template-file cloudformation-packaged.yml \
            --capabilities CAPABILITY_IAM \
            --parameter-overrides MyHostedZoneId=${MyHostedZoneId} MyHostZoneName=${MyHostZoneName} ELBHostedZoneId=${ELBHostedZoneId} \
                                  RDSUsername=${RDSUsername} RDSPassword=${RDSPassword} \
                                  WebUsename=${WebUsename} WebPassword=${WebPassword} WebEmail=${WebEmail}
