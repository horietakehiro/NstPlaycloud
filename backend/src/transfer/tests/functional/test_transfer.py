from ..common.base import BaseTestCase

from transfer.client import transfer_client
from transfer.common import config, messages

import os
from PIL import Image

class TransferTestCase(BaseTestCase):

    def test_transfer_1(self):
        """
        test_transfer_1 : receive message from sqs queue, get images from s3 bucket,
        and transfer with content and style image, and upload the resutl.
        """
        # prepare images on s3
        self.upload_image_to_s3(self.content)
        self.upload_image_to_s3(self.style)
        # prepare sqs queue message
        message = self.send_sqs_message_for_transfer()

        # main
        res = transfer_client.main()


        # assertions
        # transfer image is certainly uploaded to s3 bucket
        transfer_path = os.path.join(self.base_dir, "transfer.png")
        self.aws_s3_client.download_file(
            Filename=transfer_path,
            Bucket=config.AWS_S3_BUCKET_NAME,
            Key=self.s3_prefix + os.path.basename(transfer_path),
        )

        image = Image.open(transfer_path)

        self.assertEqual(
            res["status"], 200,
        )
        self.assertEqual(
            res["response_body"]["transfer_list"][0]["size"], image.size
        )

        content_path = os.path.join(self.test_config.IMAGE_DIR, os.path.basename(self.content))
        style_path = os.path.join(self.test_config.IMAGE_DIR, os.path.basename(self.style))
        transfer_path = os.path.join(self.test_config.IMAGE_DIR, os.path.basename(self.transfer))
        self.assertListEqual(
            [
                os.path.exists(content_path),
                os.path.exists(style_path),
                os.path.exists(transfer_path),
            ],
            [False, False, False]
        )


    def test_transfer_2(self):
        """
        test_transfer_2 : if sqs queue is not working, end with no exception.
        """
        # tempolarily delete sqs queue
        self.aws_sqs_client.delete_queue(QueueUrl=self.transfer_q_url)
        # expect no exception raises
        res = transfer_client.main()
        # restore sqs queue
        self.aws_sqs_client.create_queue(QueueName=self.test_config.AWS_SQS_TRANSFER_QUEUE_NAME)

        self.assertEqual(
            res["status"], 404,
        )
        self.assertEqual(
            res["response_body"]["messages"][0], messages.SQS_CANNOT_CONNECT.format(
                self.test_config.AWS_SQS_ENDPOINT_URL, self.test_config.AWS_SQS_TRANSFER_QUEUE_NAME
            )
        )


    def test_transfer_3(self):
        """
        test_transfer_3 : if sqs queue has not messag, end with no exception.
        """
        # make queue empty
        self.aws_sqs_client.delete_queue(QueueUrl=self.transfer_q_url)
        self.aws_sqs_client.create_queue(QueueName=self.test_config.AWS_SQS_TRANSFER_QUEUE_NAME)

        # expect no exception raises
        res = transfer_client.main()

        self.assertEqual(
            res["status"], 404,
        )
        self.assertEqual(
            res["response_body"]["messages"][0], messages.SQS_NO_MESSAGE_STORED.format(
                self.test_config.AWS_SQS_TRANSFER_QUEUE_NAME
            )
        )
    

    def test_transfer_4(self):
        """
        test_transfer_4 : if s3 bucket is not working, end with no exception.
        """
        # prepare sqs queue message
        self.send_sqs_message_for_transfer()

        # tempolarily delete s3 bucket
        self.aws_s3_resource.Bucket(
            self.test_config.AWS_S3_BUCKET_NAME
        ).objects.all().delete()
        # delete bucket
        self.aws_s3_client.delete_bucket(Bucket=self.test_config.AWS_S3_BUCKET_NAME)
        # expect no exception raises
        res = transfer_client.main()
        # restore bucket queue
        self.aws_s3_client.create_bucket(Bucket=self.test_config.AWS_S3_BUCKET_NAME)

        self.assertEqual(
            res["status"], 404,
        )
        self.assertEqual(
            res["response_body"]["messages"][0], messages.S3_CANNOT_CONNECT_DOWNLOAD.format(
                self.test_config.AWS_S3_ENDPOINT_URL, self.test_config.AWS_S3_BUCKET_NAME,
                self.transfer_queue_message["request_body"]["key_prefix"] + self.transfer_queue_message["request_body"]["content_list"][0],
                self.transfer_queue_message["request_body"]["key_prefix"] + self.transfer_queue_message["request_body"]["style_list"][0],
            )
        )



    def test_transfer_5(self):
        """
        test_transfer_5 : receive message from sqs queue, get images from s3 bucket,
        and transfer with content and style image, and upload the resutl.
        """
        # prepare images on s3
        self.upload_image_to_s3(self.content)
        self.upload_image_to_s3(self.style)
        # prepare sqs queue message
        self.send_sqs_message_for_transfer()

        # main
        res = transfer_client.main()


        # assertions
        # transfer image is certainly uploaded to s3 bucket
        transfer_path = os.path.join(self.base_dir, "transfer.png")
        self.aws_s3_client.download_file(
            Filename=transfer_path,
            Bucket=config.AWS_S3_BUCKET_NAME,
            Key=self.s3_prefix + os.path.basename(transfer_path),
        )

        image = Image.open(transfer_path)

        self.assertEqual(
            res["status"], 200,
        )
        self.assertEqual(
            res["response_body"]["transfer_list"][0]["size"], image.size
        )


