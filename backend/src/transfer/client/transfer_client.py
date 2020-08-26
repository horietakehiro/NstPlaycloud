import os
import boto3
import json

from transfer.common import config

def receive_sqs_message(config):
    """
    receive a message from sqs queue
    and return the body as dict
    """
    clinet = boto3.client("sqs", endpoint_url=config.AWS_SQS_ENDPOINT_URL)

    # get queue url
    url = clinet.get_queue_url(QueueName=config.AWS_SQS_TRANSFER_QUEUE_NAME)

    # receive one message
    resp = clinet.receive_message(QueueUrl=url["QueueUrl"])

    # convert the body into dict
    message = json.loads(resp["Messages"][0]["Body"])

    return message


def get_images_from_s3(config, message):
    """
    download content and style images from s3
    and save them on local file,
    and return these, and transfer's path
    """
    client = boto3.client("s3", endpoint_url=config.AWS_S3_ENDPOINT_URL)


    # create 3 paths from message
    content = message["request_body"]["content_list"][0]
    style = message["request_body"]["style_list"][0]
    transfer = message["request_body"]["transfer_list"][0]

    content_path = os.path.join(config.IMAGE_DIR, content)
    style_path = os.path.join(config.IMAGE_DIR, style)
    transfer_path = os.path.join(config.IMAGE_DIR, transfer)


    # download content and style images
    res = client.download_file(
        Filename=content_path,
        Bucket=message["request_body"]["bucket"],
        Key=message["request_body"]["key_prefix"] + content
    )

    res = client.download_file(
        Filename=style_path,
        Bucket=message["request_body"]["bucket"],
        Key=message["request_body"]["key_prefix"] + style
    )

    return content_path, style_path, transfer_path



def preprocess_image():
    pass

def call_engine():
    pass

def put_image_to_s3():
    pass


def main():
    
    # receive sqs message as dict
    message = receive_sqs_message(config)

    # get content and style images from s3, and return these and transfer's path
    content_path, style_path, transfer_path = get_images_from_s3(config, message)
    
    # preprocess image and return as ndarray
    content = preprocess_image(config, content_path)
    style = preprocess_image(config, style_path)

    # call engine
    transfer = call_engine(config, content=content, style=style, transfer=content)

    # put transfer image to s3
    res = put_image_to_s3(config, message, transfer_path, transfer)
    
    return {
        "status" : 200,
        "response_body" : {
            "image_name" : os.path.basename(transfer_path),
            "size" : transfer.shape[1:-1:-1]
        }
    }

