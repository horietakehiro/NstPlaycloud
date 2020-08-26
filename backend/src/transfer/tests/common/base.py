import unittest

import os
import glob
import json
import boto3
import shutil

from transfer.common import config

class BaseTestCase(unittest.TestCase):

    base_dir = os.path.join(os.path.dirname(__file__), "..", "test_datas")
    test_config = config
    test_config.IMAGE_DIR = test_config.IMAGE_DIR.replace("/images", "images4test")


    transfer = os.path.join(base_dir, "transfer.png")
    content = os.path.join(base_dir, "content.png")
    style = os.path.join(base_dir, "style.png")
    invalid = os.path.join(base_dir, "invalid.png")

    s3_prefix = "media/original/raw/"


    aws_sqs_client = None
    aws_s3_client = None
    aws_s3_resource = None
    transfer_q_url = None

    transfer_queue_message = {
        "request_type" : "transfer",
        "request_body" : {
            "transfer_list" : None,
            "content_list" : None,
            "style_list" : None,

            "key_prefix" : "media/original/raw/",
            "bucket" : test_config.AWS_S3_BUCKET_NAME,
            "s3_endpoint" : test_config.AWS_S3_ENDPOINT_URL,
        }
    }


    
    @classmethod
    def setUpClass(cls):
        cls.aws_s3_client = boto3.client("s3", endpoint_url=cls.test_config.AWS_S3_ENDPOINT_URL)
        cls.aws_s3_resource = boto3.resource("s3", endpoint_url=cls.test_config.AWS_S3_ENDPOINT_URL)
        cls.aws_s3_client.create_bucket(Bucket=cls.test_config.AWS_S3_BUCKET_NAME)

        # create queue for test
        cls.aws_sqs_client = boto3.client("sqs", endpoint_url=cls.test_config.AWS_SQS_ENDPOINT_URL)

        res = cls.aws_sqs_client.create_queue(QueueName=cls.test_config.AWS_SQS_TRANSFER_QUEUE_NAME)
        cls.transfer_q_url = res["QueueUrl"]

        os.makedirs(cls.test_config.IMAGE_DIR, exist_ok=True)


        return super().setUpClass()

    def setUp(self):
        return super().setUp()

    @classmethod
    def tearDownClass(cls):
        # delete all objects
        cls.aws_s3_resource.Bucket(
            cls.test_config.AWS_S3_BUCKET_NAME
        ).objects.all().delete()
        # delete bucket
        cls.aws_s3_client.delete_bucket(Bucket=cls.test_config.AWS_S3_BUCKET_NAME)

        # delete queue
        cls.aws_sqs_client.delete_queue(QueueUrl=cls.transfer_q_url)


        shutil.rmtree(cls.test_config.IMAGE_DIR)

        return super().tearDownClass()

    def tearDown(self):
        # delete all objects
        self.aws_s3_resource.Bucket(
            self.test_config.AWS_S3_BUCKET_NAME
        ).objects.all().delete()

        # delete all images in image dir
        files = glob.glob(os.path.join(self.test_config.IMAGE_DIR, "*"))
        for f in files:
            try:
                os.remove(f)
            except FileNotFoundError:
                pass

        return super().tearDown()

    def upload_image_to_s3(self, image_path):
        """
        upload image to s3, according to sqs message
        """

        self.aws_s3_client.upload_file(
            Filename=image_path,
            Bucket=self.test_config.AWS_S3_BUCKET_NAME,
            Key=self.s3_prefix + os.path.basename(image_path),
        )

    def send_sqs_message_for_transfer(self, content_list=None, style_list=None, transfer_list=None):
        message = self.transfer_queue_message

        if content_list is None:
            message["request_body"]["content_list"] = [os.path.basename(self.content)]
        else:
            message["request_body"]["content_list"] = content_list
        if style_list is None:
            message["request_body"]["style_list"] = [os.path.basename(self.style)]
        else:
            message["request_body"]["style_list"] = style_list
        if transfer_list is None:
            message["request_body"]["transfer_list"] = [os.path.basename(self.transfer)]
        else:
            message["request_body"]["transfer_list"] = transfer_list

        self.aws_sqs_client.send_message(
            QueueUrl=self.transfer_q_url,
            MessageBody=json.dumps(message),
        )


