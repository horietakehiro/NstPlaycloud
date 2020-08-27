import os
import boto3
import json
import copy
import numpy as np
from PIL import Image

from transfer.common import config
from transfer.engine.core import NstEngine

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


def preprocess_image(config, image_path):
    """
    return image as ndarray
    shape : (1, max(config.IMAGE_MAX_SIZE), max(config.IMAGE_MAX_SIZE), 3)
    scale : 0 ~ 1
    dtyle : np.float32
    """
    image = Image.open(image_path)
    # forcing convert to RGB(3 channel)
    image = image.convert("RGB")

    # limit the image size to config.IMAGE_MAX_SIZE
    current_size = image.size
    scale = config.MAX_IMAGE_SIZE / max(current_size)
    new_size = (round(s * scale) for s in current_size)
    image = image.resize(new_size)

    # convert dtype
    image = np.array(image, dtype=np.float32)
    # scale value
    image = image / image.max(axis=None)
    # add new asix
    image = image[np.newaxis, ]

    return image

def call_engine(config, content, style):
    """
    initiate NstEngine, call it, and return transfer result
    """
    # initiate engine with config
    height, width = content.shape[1:3]
    engine = NstEngine(height, width, config)

    transfer = copy.deepcopy(content)

    transfer = engine.fit(content=transfer, style=style, content_org=content)

    return transfer


def postprocess_image(config, transfer, transfer_path):
    """
    save transfer result as local image file
    inputted transfer array should be :
        dtype : np.float32
        scale : 0 ~ 1
        shape : [1, X, X, 3]
    """
    # reshape to (X, X, 3)
    transfer = transfer[0, :, :, :]

    # scale to 0 ~ 255
    transfer = transfer * 255.

    # convert dtype into np.uint8
    transfer = transfer.astype(np.uint8)

    # convert into PIL image
    transfer = Image.fromarray(transfer, mode="RGB")

    # save
    transfer.save(transfer_path)

    return transfer_path


def put_image_to_s3(config, message, transfer_path):
    """
    upload transfer image to s3
    """
    # create transfer key name
    key = message["request_body"]["key_prefix"] + os.path.basename(transfer_path)
    bucket = message["request_body"]["bucket"]

    client = boto3.client("s3", endpoint_url=config.AWS_S3_ENDPOINT_URL)
    ret = client.upload_file(Filename=transfer_path, Bucket=bucket, Key=key)
    
    return ret

def main():
    
    # receive sqs message as dict
    message = receive_sqs_message(config)

    # get content and style images from s3, and return these and transfer's path
    content_path, style_path, transfer_path = get_images_from_s3(config, message)
    
    # preprocess image and return as ndarray
    content = preprocess_image(config, content_path)
    style = preprocess_image(config, style_path)

    # call engine
    transfer = call_engine(config, content=content, style=style)

    # postprocess transfer image
    transfer_path = postprocess_image(config, transfer, transfer_path)

    # put transfer image to s3
    res = put_image_to_s3(config, message, transfer_path)
    
    return {
        "status" : 200,
        "response_body" : {
            "image_name" : os.path.basename(transfer_path),
            "size" : transfer.shape[1:-1:-1]
        }
    }

