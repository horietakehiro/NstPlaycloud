import os
import re
import json
from PIL import Image

import boto3
import botocore

def fetch_record(event):
    """
    return each record's bucket name and object(key) name as generator
    """
    _event = event
    def _fetch():
        for record in _event["Records"]:
            bucket = record["s3"]["bucket"]["name"]
            objkey = record["s3"]["object"]["key"]

            yield bucket, objkey
    return _fetch()

def download_file(client, bucket, objkey, image_dir):
    """
    download file from s3 bucket and save under the image_dir
    """
    basename = objkey.split("/")[-1]
    save_path = os.path.join(image_dir, basename)

    try:
        client.download_file(bucket, objkey, save_path)

    except botocore.exceptions.ClientError:
        return {"status" : 404, "message" : f"{bucket}/{objkey} is not found"}
    except botocore.exceptions.EndpointConnectionError:
        return {"status" : 404, "message" : f"cannot connect to {str(client._endpoint)}"}
    return None

def create_thumbnail(objkey, image_dir):
    """
    create thumbnail image(224, 224) and overwrite its original image.
    """
    path = os.path.join(image_dir, objkey.split("/")[-1])

    try:
        image = Image.open(path)
        image = image.resize((112, 112))
        image.save(path)
    except:
        return {"message" : 500, "message" : f"{path} is invalid image"}

    return None

def upload_file(client, bucket, objkey, image_dir):
    """
    upload thumbnail image.
    """
    new_objkey = re.sub(r"/original/", "/thumbnail/", objkey)
    path = os.path.join(image_dir, new_objkey.split("/")[-1])

    try:
        client.upload_file(path, bucket, new_objkey)
    except botocore.exceptions.EndpointConnectionError:
        return {"status" : 404, "message" : f"cannot connect to {str(client._endpoint)}"}

    return None


def lambda_handler(event, context):
    """
    This lambda is called by s3 put event.
    creating a thumbnail image(224,224) from an original image
    specified in event records, and finally upload it.
    """


    record_gen = fetch_record(event)
    image_dir = os.environ.get("IMAGE_DIR", "/tmp")

    client = boto3.client("s3", endpoint_url=os.environ.get("S3_ENDPOINT", None))

    try:
        for bucket, objkey in record_gen:
            # downalod
            ret = download_file(client, bucket, objkey, image_dir)
            if ret is not None:
                return json.dumps(ret)
            
            # create thumbnail
            ret = create_thumbnail(objkey, image_dir)
            if ret is not None:
                return json.dumps(ret)

            ret = upload_file(client, bucket, objkey, image_dir)
            if ret is not None:
                return json.dumps(ret)
    finally:
        filename = os.path.join(image_dir, objkey.split("/")[-1])
        if os.path.exists(filename):
            os.remove(filename)

    return json.dumps({"status" :  200})