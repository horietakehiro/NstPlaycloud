import os
import boto3
import json
import copy
import numpy as np
from PIL import Image

from transfer.common import config, messages, exceptions
from transfer.engine.core import NstEngine

def receive_sqs_message(config):
    """
    receive a message from sqs queue
    each body in messages are dict and return them as list.
    """
    clinet = boto3.client("sqs", endpoint_url=config.AWS_SQS_ENDPOINT_URL, region_name=config.AWS_REGION)
    try:
        # get queue url
        url = clinet.get_queue_url(QueueName=config.AWS_SQS_TRANSFER_QUEUE_NAME)
        # receive messages as many as possible
        resp = clinet.receive_message(QueueUrl=url["QueueUrl"], MaxNumberOfMessages=10)
    except:
        raise exceptions.SQSConnectionError(config.AWS_SQS_ENDPOINT_URL, config.AWS_SQS_TRANSFER_QUEUE_NAME)


    try:
        message_list = [json.loads(message["Body"]) for message in resp["Messages"]]
    except:
        # in case no messages are stored in sqs queue
        raise exceptions.SQSNoMessageError(config.AWS_SQS_ENDPOINT_URL, config.AWS_SQS_TRANSFER_QUEUE_NAME)

    return message_list
    # return message_list


def get_images_from_s3(config, message):
    """
    download content and style images from s3
    and save them on local file,
    and return these, and transfer's path as list
    """
    client = boto3.client("s3", endpoint_url=message["request_body"]["s3_endpoint"], region_name=config.AWS_REGION)

    path_list = []
    content_list = message["request_body"]["content_list"]
    style_list = message["request_body"]["style_list"]
    transfer_list = message["request_body"]["transfer_list"]

    for content, style, transfer in zip(content_list, style_list, transfer_list):

        # create 3 paths from message
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
            raise exceptions.S3DownloadError(
                transfer, message["request_body"]["s3_endpoint"], message["request_body"]["bucket"], content, style 

            )


        path_list.append([content_path, style_path, transfer_path])

    return path_list


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

    client = boto3.client("s3", endpoint_url=message["request_body"]["s3_endpoint"], region_name=config.AWS_REGION)
    try:
        client.upload_file(Filename=transfer_path, Bucket=bucket, Key=key)
    except:
        raise exceptions.S3UploadError(
            os.path.basename(transfer_path), message["request_body"]["s3_endpoint"], bucket
        )
    
    return None

def main():

    response = copy.deepcopy(messages.RESPONSE_BODY)
    # receive sqs message list. each message are dict
    try:
        message_list = receive_sqs_message(config)
    except exceptions.SQSConnectionError as ex:
        response["message_list"].append(ex.get_message())
        return response
    except exceptions.SQSNoMessageError as ex:
        response["message_list"].append(ex.get_message())
        return response


    # processing according to each message
    for message in message_list:
        path_list = None
        try:
            # get content and style images from s3, and return these and transfer's path as list
            # e.g. [["content_path", "style_path", "transfer_path"], ["content_path", "style_path", "transfer_path"]]
            try:
                path_list = get_images_from_s3(config, message)
            except exceptions.S3DownloadError as ex:
                response["message_list"].append(ex.get_message())
                continue
    

            for content_path, style_path, transfer_path in path_list:
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
                try:
                    res = put_image_to_s3(config, message, transfer_path)
                except exceptions.S3UploadError as ex:
                    response["message_list"].append(
                        ex.get_message()
                    )
                    continue

            

                response["message_list"].append(
                    messages.TRANSFER_SUCCESS.format(
                        os.path.basename(transfer_path), transfer.shape[-2:0:-1]
                    )
                )
        finally:
            if path_list is not None:
                path_list = [p for paths in path_list for p in paths]
                for path in path_list:
                    try:
                        os.remove(path)
                    except FileNotFoundError:
                        pass

    return response

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
    run_locally(*sys.argv[1:])
    end = time.time()

    print(round(end - start))

