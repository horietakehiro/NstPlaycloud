from urllib.parse import urlparse

import os
import json
import copy
import boto3
import botocore
from glob import glob

import cv2
import numpy as np
from PIL import Image

def get_params(event):
    """
    validate event["body] field
        - s3_endpoint(optional) : string
        - bucket(required) : url formatted string
        - content(required) : string
        - transfer(required) : string

    and return the three params as dict
    """
    retdict = {"statusCode" : 200, "body" : ""}

    # body validation
    try:
        body = json.loads(event["body"])
    except KeyError:
        retdict["statusCode"] = 400
        retdict["body"] = f"body is empty"
        return retdict
    except TypeError:
        retdict["statusCode"] = 400
        retdict["body"] = f"body is empty"
        return retdict
    except json.JSONDecodeError:
        retdict["statusCode"] = 400
        retdict["body"] = f"body : {event['body']} is invalid"
        return retdict
        

    
    # s3_endpoint validation
    try:
        s3_endpoint = body["s3_endpoint"]
    except KeyError:
        retdict["statusCode"] = 400
        retdict["body"] = "field : s3_endpoint does not exist"
        return retdict
    if s3_endpoint is not None:
        try:
            parsed = urlparse(s3_endpoint)
        except:
            parsed = None
        if parsed is None or not all([parsed.scheme, parsed.netloc]):
            retdict["statusCode"] = 400
            retdict["body"] = f"s3_endpoint : {s3_endpoint} is invalid"
            return retdict

    # bucket validation
    try:
        bucket = body["bucket"]
    except KeyError:
        retdict["statusCode"] = 400
        retdict["body"] = "field : bucket does not exist"
        return retdict
    if bucket is None:
        retdict["statusCode"] = 400
        retdict["body"] = f"bucket is empty"
        return retdict

    # content validation
    try:
        content = body["content"]
    except KeyError:
        retdict["statusCode"] = 400
        retdict["body"] = "field : content does not exist"
        return retdict
    if content is None:
        retdict["statusCode"] = 400
        retdict["body"] = f"content is empty"
        return retdict

    # transfer validation
    try:
        transfer = body["transfer"]
    except KeyError:
        retdict["statusCode"] = 400
        retdict["body"] = "field : transfer does not exist"
        return retdict
    if transfer is None:
        retdict["statusCode"] = 400
        retdict["body"] = f"transfer is empty"
        return retdict

    retdict["s3_endpoint"] = s3_endpoint
    retdict["bucket"] = bucket
    retdict["content"] = content
    retdict["transfer"] = transfer
    return retdict

def download_file(client, bucket, objkey, image_dir):
    """
    download file from s3 bucket and save under the image_dir
    """
    basename = objkey.split("/")[-1]
    save_path = os.path.join(image_dir, basename)

    try:
        client.download_file(bucket, objkey, save_path)

    except botocore.exceptions.ClientError:
        return {"statusCode" : 404, "body" : f"{bucket}/{objkey} is not found"}
    except botocore.exceptions.EndpointConnectionError:
        return {"statusCode" : 404, "body" : f"cannot connect to {str(client._endpoint)}"}
    return None


def mask_image(content, transfer, image_dir):
    """
    create 4 types of images and save under image_dir.
    filenames created are "HOGEHOGE_${transfer_filename}"
    """

    masking_path = os.path.join(image_dir, content.split("/")[-1])
    transfer_path = os.path.join(image_dir, transfer.split("/")[-1])

    masked_path = os.path.join(image_dir, "masked____" + transfer.split("/")[-1])
    masked_inv_path = os.path.join(image_dir, "masked_inv____" + transfer.split("/")[-1])
    binned_path = os.path.join(image_dir, "binned____" + transfer.split("/")[-1])
    binned_inv_path = os.path.join(image_dir, "binned_inv____" + transfer.split("/")[-1])


    masking = Image.open(masking_path).convert("RGB")
    masked = Image.open(transfer_path).convert("RGB")

    # adjust masking image's size with masked image
    if masking.size != masked.size:
        masking = masking.resize(masked.size)
    
    # convert into ndarray
    masking = np.array(masking)
    masked = np.array(masked)
    masked_inv = copy.deepcopy(masked)

    gray = cv2.cvtColor(masking, cv2.COLOR_RGB2GRAY)
    _, binned = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU)
    _, binned_inv = cv2.threshold(gray, 0, 255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)

    for h in range(binned.shape[0]):
        for w in range(binned.shape[1]):
            if binned[h,w]:
                masked[h,w,:] = masking[h,w,:]
            if binned_inv[h,w]:
                masked_inv[h,w,:] = masking[h,w,:]


    Image.fromarray(masked).save(masked_path)
    Image.fromarray(masked_inv).save(masked_inv_path)
    Image.fromarray(binned).save(binned_path)
    Image.fromarray(binned_inv).save(binned_inv_path)
    
    return None



def upload_files(client, bucket, transfer, image_dir):
    """
    upload 4images created from transfer image.
    """

    files = glob(os.path.join(image_dir, "*____" + transfer.split("/")[-1]))

    for file in files:
        try:
            prefix = "_".join(file.split("/")[-1].split("____")[:-1])
            client.upload_file(file, bucket, transfer.replace("/raw/", f"/{prefix}/"))
        except botocore.exceptions.EndpointConnectionError:
            return {"statusCode" : 404, "body" : f"cannot connect to {str(client._endpoint)}"}

    return None



def lambda_handler(event, context):
    """
    execute masking to an image specified in 3s bucket.
    this lambda called via api-gateway
    """

    # get request params
    params = get_params(event)
    if params["statusCode"] != 200:
        return params

    # download images from s3
    try:
        client = boto3.client("s3", endpoint_url=os.environ.get("S3_ENDPOINT", params["s3_endpoint"]))
        image_dir = os.environ.get("IMAGE_DIR", "/tmp")
        ret = download_file(client, params["bucket"], params["content"], image_dir)
        if ret is not None:
            return ret
        ret = download_file(client, params["bucket"], params["transfer"], image_dir)
        if ret is not None:
            return ret


        # masking image
        ret = mask_image(params["content"], params["transfer"], image_dir)
        if ret is not None:
            return ret

        # upload 4 images to s3
        ret = upload_files(client, params["bucket"], params["transfer"], image_dir)
        if ret is not None:
            return ret

    finally:
        # remove all 6 files
        files = [
            os.path.join(image_dir, params["content"].split("/")[-1]),
            os.path.join(image_dir, params["transfer"].split("/")[-1]),
            
        ]
        files.extend(glob(os.path.join(image_dir, "*_" + params["transfer"].split("/")[-1])))
        for file in files:
            try:
                os.remove(file)
            except FileNotFoundError:
                pass
    
    return {"statusCode" : 200, "body" : None}
