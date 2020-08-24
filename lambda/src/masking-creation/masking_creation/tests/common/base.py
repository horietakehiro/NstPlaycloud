import unittest

import os
import json
from glob import glob

import boto3

class BaseTestCase(unittest.TestCase):

    test_event_base_dir = os.path.join(
        os.path.dirname(__file__), "..", "test_events"
    )

    image_dir = "/tmp"
    s3_endpoint = os.environ.get("S3_ENDPOINT", "http://docker.for.mac.localhost:4566")
    bucket = "test-bucket"
    # objkey = "original/raw/sample.png"
    content = "original/raw/content.png"
    transfer = "original/raw/transfer.png"

    filename = os.path.join(
        os.path.dirname(__file__), "..", "test_datas", "sample.png"
    )

    client = boto3.client("s3", endpoint_url=s3_endpoint)
    resource = boto3.resource("s3", endpoint_url=s3_endpoint)


    @classmethod
    def setUpClass(cls):
        
        cls.client.create_bucket(Bucket=cls.bucket)
        # cls.client.upload_file(cls.filename, cls.bucket, cls.objkey)
        cls.client.upload_file(cls.filename, cls.bucket, cls.content)
        cls.client.upload_file(cls.filename, cls.bucket, cls.transfer)
        return super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        bucket = cls.resource.Bucket(cls.bucket)
        bucket.objects.all().delete()
        bucket.delete()
        return super().tearDownClass()

    def setUp(self):
        return super().setUp()

    def tearDown(self):
        picfiles = glob(os.path.join(self.image_dir, "*.png"))
        for file in picfiles:
            try:
                os.remove(file)
            except FileNotFoundError:
                pass

        return super().tearDown()


    def load_event(self, filename, dirname=None):
        if dirname is None:
            dirname = self.test_event_base_dir
        path = os.path.join(dirname, filename)

        if not os.path.exists(path):
            self.fail(f"{path} is not found.")

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
