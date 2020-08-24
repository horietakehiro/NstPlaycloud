import unittest
from unittest.mock import patch
from ..common.base import BaseTestCase

import os
import re
from PIL import Image

import boto3
import botocore


from thumbnail_creation import app

class AppTestCase(BaseTestCase):

    def test_return_one_record_from_single_record(self):
        event = self.load_event("single-record.json")

        record_gen = app.fetch_record(event)
        bucket, objkey = next(record_gen)

        self.assertListEqual(
            [bucket, objkey], 
            [
                event["Records"][0]["s3"]["bucket"]["name"],
                event["Records"][0]["s3"]["object"]["key"],
            ],
        )

    def test_return_two_redord_from_multiple_record(self):
        event = self.load_event("multiple-record.json")

        buckets, objkeys = [], []
        record_gen = app.fetch_record(event)
        for b, k in record_gen:
            buckets.append(b)
            objkeys.append(k)

        self.assertListEqual(
            [buckets, objkeys], 
            [
                [
                    event["Records"][0]["s3"]["bucket"]["name"],
                    event["Records"][1]["s3"]["bucket"]["name"],
                ],
                [
                    event["Records"][0]["s3"]["object"]["key"],
                    event["Records"][1]["s3"]["object"]["key"],
                ]
            ],
        )

    def test_download_and_save_image_from_s3(self):

        ret = app.download_file(self.client, self.bucket, self.objkey, image_dir=self.image_dir)

        self.assertTrue(
            os.path.exists(os.path.join(
                self.image_dir, self.objkey.split("/")[-1]
            ))
        )

    def test_return_error_message_if_bucket_not_found(self):
        ret = app.download_file(self.client, "not-found-bucket", self.objkey, image_dir=self.image_dir)

        self.assertDictEqual(
            ret,
            {"status" : 404, "message" : f"not-found-bucket/{self.objkey} is not found"},
        )

    def test_return_error_result_if_objkey_not_found(self):
        ret = app.download_file(self.client, self.bucket, "not-found-objkey", image_dir=self.image_dir)

        self.assertDictEqual(
            ret,
            {"status" : 404, "message" : f"{self.bucket}/not-found-objkey is not found"},
        )

    def test_return_error_result_if_endpoint_cannot_connects_download(self):
        invalid_client = boto3.client("s3", endpoint_url="http://notfoundendpoint")
        ret = app.download_file(invalid_client, self.bucket, self.objkey, image_dir=self.image_dir)

        self.assertDictEqual(
            ret,
            {"status" : 404, "message" : f"cannot connect to {str(invalid_client._endpoint)}"},
        )

    def test_downloaded_image_overwrited_by_thumbnail(self):
        ret = app.download_file(self.client, self.bucket, self.objkey, image_dir=self.image_dir)

        ret = app.create_thumbnail(self.objkey, self.image_dir)

        path = os.path.join(
            self.image_dir, self.objkey.split("/")[-1]
        )
        image = Image.open(path)

        self.assertTupleEqual(
            image.size, (224, 224),
        )

    def test_return_error_result_if_invalid_image(self):
        filename = os.path.join(
            os.path.dirname(__file__), "..","test_datas", "invalid.png"
        )
        objkey = filename.split("/")[-1]
        self.client.upload_file(filename ,self.bucket, objkey)
        ret = app.download_file(self.client, self.bucket, objkey, image_dir=self.image_dir)

        ret = app.create_thumbnail(objkey, self.image_dir)

        self.assertDictEqual(
            ret,
            {"message" : 500, "message" : f"{os.path.join(self.image_dir, objkey)} is invalid image"}
        )


    def test_upload_thumbnail_image_to_s3(self):
        ret = app.upload_file(self.client, self.bucket, self.objkey, self.image_dir)

        new_objkey = re.sub(r"^original/", "thumbnail/", self.objkey)

        ret = self.client.list_objects(Bucket=self.bucket)
        key_list = [content["Key"] for content in ret["Contents"]]
        self.assertIn(
            new_objkey, key_list
        )

    def test_cat_upload_thumbnail_image_if_already_uploaded(self):
        ret = app.download_file(self.client, self.bucket, self.objkey, image_dir=self.image_dir)
        ret = app.upload_file(self.client, self.bucket, self.objkey, self.image_dir)

        new_objkey = re.sub(r"^original/", "thumbnail/", self.objkey)

        ret = self.client.list_objects(Bucket=self.bucket)
        key_list = [content["Key"] for content in ret["Contents"]]
        self.assertIn(
            new_objkey, key_list
        )

    def test_return_error_result_if_endpoint_cannot_connects_uploaed(self):
        invalid_client = boto3.client("s3", endpoint_url="http://notfoundendpoint")
        ret = app.upload_file(invalid_client, self.bucket, self.objkey, self.image_dir)

        self.assertDictEqual(
            ret,
            {"status" : 404, "message" : f"cannot connect to {str(invalid_client._endpoint)}"},
        )



