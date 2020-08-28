import unittest

import os
import json

import boto3

class BaseTestCase(unittest.TestCase):

    test_event_base_dir = os.path.join(
        os.path.dirname(__file__), "..", "test_events"
    )

    image_dir = "/tmp"
    s3_endpoint = os.environ.get("S3_ENDPOINT", "http://docker.for.mac.localhost:4566")
    bucket = "test-bucket"
    key_prefixes = [
        "media/original/raw/",
        "media/original/masked/",
        "media/original/masked_inv/",
        "media/original/binned/",
        "media/original/binned_inv/",
        "media/thumbnail/raw/",
        "media/thumbnail/masked/",
        "media/thumbnail/masked_inv/",
        "media/thumbnail/binned/",
        "media/thumbnail/binned_inv/",
    ]
    
    image_path_1 = os.path.join(
        os.path.dirname(__file__), "..", "test_datas", "sample.png"
    )
    image_path_2 = os.path.join(
        os.path.dirname(__file__), "..", "test_datas", "sample_2.png"
    )

    aws_s3_client = boto3.client("s3", endpoint_url=s3_endpoint)
    aws_s3_resource = boto3.resource("s3", endpoint_url=s3_endpoint)


    @classmethod
    def setUpClass(cls):
        cls.aws_s3_client.create_bucket(Bucket=cls.bucket)

        return super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        bucket = cls.aws_s3_resource.Bucket(cls.bucket)
        bucket.objects.all().delete()
        bucket.delete()

        return super().tearDownClass()

    def setUp(self):
        return super().setUp()

    def tearDown(self):
        bucket = self.aws_s3_resource.Bucket(self.bucket)
        bucket.objects.all().delete()
        
        return super().tearDown()


    def load_event(self, filename, dirname=None):
        if dirname is None:
            dirname = self.test_event_base_dir
        path = os.path.join(dirname, filename)

        if not os.path.exists(path):
            self.fail(f"{path} is not found.")

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # def overwrite_event(self, event, bucket=None, objkey=None):
    #     event["Records"][0]["s3"]["bucket"]["name"] = self.bucket if bucket is None else bucket
    #     event["Records"][0]["s3"]["object"]["key"] = self.objkey if objkey is None else objkey

    #     return event

    def upload_images(self, image_path):
        for prefix in self.key_prefixes:
            key = prefix + os.path.basename(image_path)

            self.aws_s3_client.upload_file(
                Filename=image_path, 
                Bucket=self.bucket, 
                Key=key
            )
        