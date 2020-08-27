import os
import boto3
import json
import copy
import numpy as np
from PIL import Image

from transfer.common import config, messages
from transfer.engine.core import NstEngine

def receive_sqs_message(config):
    """
    receive a message from sqs queue
    and return the body as dict
    """
    clinet = boto3.client("sqs", endpoint_url=config.AWS_SQS_ENDPOINT_URL)
    
    try:
        # get queue url
        url = clinet.get_queue_url(QueueName=config.AWS_SQS_TRANSFER_QUEUE_NAME)
        # receive one message
        resp = clinet.receive_message(QueueUrl=url["QueueUrl"])
    except:
        return messages.SQS_CANNOT_CONNECT.format(
            config.AWS_SQS_ENDPOINT_URL, config.AWS_SQS_TRANSFER_QUEUE_NAME
        )

    try:
        # convert the body into dict
        message = json.loads(resp["Messages"][0]["Body"])
    except:
        # in case no messages are stored in sqs queue
        return messages.SQS_NO_MESSAGE_STORED.format(
            config.AWS_SQS_TRANSFER_QUEUE_NAME
        )


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

    try:
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
    except:
        return None, None, None

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
    try:
        client.upload_file(Filename=transfer_path, Bucket=bucket, Key=key)
    except:
        return messages.S3_CANNOT_CONNECT_UPLOAD.format(
            config.AWS_S3_ENDPOINT_URL, config.AWS_S3_BUCKET_NAME,
            transfer_path,
        )

    
    return None

def main():
    
    # receive sqs message as dict
    message = receive_sqs_message(config)
    if isinstance(message, str):
        return {
            "status" : 404,
            "response_body" : {
                "messages" : [
                    message
                ],
            },
        }

    try:
        # get content and style images from s3, and return these and transfer's path
        content_path, style_path, transfer_path = get_images_from_s3(config, message)
        if content_path is None or style_path is None:
            key_prefix = message["request_body"]["key_prefix"]
            return {
                "status" : 404,
                "response_body" : {
                    "messages" : [
                        messages.S3_CANNOT_CONNECT_DOWNLOAD.format(
                            config.AWS_S3_ENDPOINT_URL, config.AWS_S3_BUCKET_NAME,
                            key_prefix + message["request_body"]["content_list"][0],
                            key_prefix + message["request_body"]["style_list"][0],
                        )
                    ],
                },
            }

        # preprocess image and return as ndarray
        # no need to consder exception
        content = preprocess_image(config, content_path)
        style = preprocess_image(config, style_path)

        # call engine
        # no need to consder exception
        transfer = call_engine(config, content=content, style=style)

        # postprocess transfer image
        # no need to consder exception
        transfer_path = postprocess_image(config, transfer, transfer_path)

        # put transfer image to s3
        res = put_image_to_s3(config, message, transfer_path)
        if isinstance(res, str):
            return {
                "status" : 404,
                "response_body" : {
                    "messages" : [
                        res
                    ],
                },
            }
        
        
        return {
            "status" : 200,
            "response_body" : {
                "transfer_list" : [
                    {
                        "image_name" : os.path.basename(transfer_path),
                        "size" : transfer.shape[-2:0:-1],
                    },
                ],
            },
        }

    finally:
        # cleanup all local images
        def cleanup_file(path):
            try:
                os.remove(path)
            except FileNotFoundError:
                pass
        
        if content_path is not None:
            cleanup_file(content_path)
        if style_path is not None:
            cleanup_file(style_path)
        if transfer_path is not None:
            cleanup_file(transfer_path)


def run_locally(content_path, style_path, transfer_path):
    # preprocess image and return as ndarray
    content = preprocess_image(config, content_path)
    style = preprocess_image(config, style_path)

    # call engine
    transfer = call_engine(config, content=content, style=style)


    # postprocess transfer image
    transfer_path = postprocess_image(config, transfer, transfer_path)


if __name__ == "__main__":

    import sys
    import time
    start = time.time()
    print(sys.argv)
    run_locally(*sys.argv[1:])

    end = time.time()

    print(round(end - start))

