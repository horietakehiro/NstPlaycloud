import json

import boto3

def delete_images(message):
    """
    according to sqs message, delete all images at s3 bucket
    if succeed, return None
    """
    # delete = {
    #     'Objects': [
    #         {
    #             'Key': 'string',
    #         },
    #     ],
    # }

    # create args for deletion
    body = message["request_body"]
    bucket = body["bucket"]
    endpoint = body["s3_endpoint"]
    # message may contain multiple image record
    objects = [
        {"Key" : prefix + basename} 
        for basename in body["basenames"]
        for prefix in body["prefixes"]
    ]

    client = boto3.client("s3", endpoint_url=endpoint)
    try:
        ret = client.delete_objects(Bucket=bucket, Delete={"Objects" : objects})
    except:
        return "Cannot connect to s3 endpoint : {}, or bucket : {} doest not exist".format(
            endpoint, bucket
        )

    return None


def lambda_handler(event, context):
    """
    This lambda is called by sqs event.
    delete all images, which specified in sqs message, at s3 bucket 
    """

    for record in event["Records"]:
        message = json.loads(record["body"])

        ret = delete_images(message)
        if ret is not None:
            return {
                "status" : 404,
                "message" : ret,
            }


    return {
        "status" : 200,
    }
