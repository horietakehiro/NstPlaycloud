# NstPlaycloud
NstPlaycloud provides you a playground on your web browser, where you can try [Neural Style Transfer](https://www.tensorflow.org/tutorials/generative/style_transfer) with any images you like. This app is designed to be deployed on AWS, so it's named as  play**cloud**, instead of play**ground**.

## Prerequirement(AWS)
- Route53 Domain
- Keypair for EC2 instances

## Prerequirement(local)
- Linux or Mac OS machine
- [AWS CLIv2](https://docs.aws.amazon.com/ja_jp/cli/latest/userguide/install-cliv2.html)
- [SAM](https://docs.aws.amazon.com/ja_jp/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
- [jq](https://stedolan.github.io/jq/download/)
- creating the file : "secrets" for secret parameters by refering to "secrets.org"

## Deployment
1. Clone this repository
2. Run the deployment script : `./aws-deploy-stack.sh`
3. After Deployment has completed, you can access the web page : https://nstpc.YOUR_OWN_DOMAIN.com/

## Cleanup
1. Clone this repository
2. Run the cleanup script : `./aws-cleanup-stack.sh`
3. All images stored on s3 bucket are automatically downloaded on : `./backups/YYYYMMDD-hhmmss/original/`
4. Cleanup script waits until the stack deletion completes.
