from ..common.base import BaseTestCase

from transfer.client import transfer_client
from transfer.common import config, messages

import os
import glob
from PIL import Image

class TransferTestCase(BaseTestCase):

    def test_transfer_1(self):
        """
        test_transfer_1 : success case.
        receive message from sqs queue, get images from s3 bucket,
        and transfer with content and style image, and upload the resutl.
        """
        # prepare images on s3
        self.upload_image_to_s3(self.content)
        self.upload_image_to_s3(self.content.replace("content.png", "content_2.png"))
        self.upload_image_to_s3(self.content.replace("content.png", "content_3.png"))
        self.upload_image_to_s3(self.style)
        self.upload_image_to_s3(self.style.replace("style.png", "style_2.png"))
        self.upload_image_to_s3(self.style.replace("style.png", "style_3.png"))


        # prepare sqs queue message
        content_list = ["content_2.png", "content_3.png"]
        style_list = ["style_2.png", "style_3.png"]
        transfer_list = ["transfer_2.png", "transfer_3.png"]
        message = self.send_sqs_message_for_transfer()
        message = self.send_sqs_message_for_transfer(
            content_list=content_list, style_list=style_list, transfer_list=transfer_list
        )

        # run main function
        res = transfer_client.main()

        # assertions
        transfer_path_list = [
            os.path.join(self.base_dir, "transfer.png"),
            os.path.join(self.base_dir, "transfer_2.png"),
            os.path.join(self.base_dir, "transfer_3.png"),
        ]

        message_list = res["message_list"]
        self.assertEqual(len(message_list), 3)
        for i, (transfer_path, message) in enumerate(zip(transfer_path_list, message_list)):
            self.aws_s3_client.download_file(
                Filename=transfer_path,
                Bucket=config.AWS_S3_BUCKET_NAME,
                Key=self.s3_prefix + os.path.basename(transfer_path),
            )
            image = Image.open(transfer_path)
            self.assertEqual(
                message, messages.TRANSFER_SUCCESS.format(
                    os.path.basename(transfer_path), image.size
                )
            )

        self.assertEqual(len(glob.glob(os.path.join(self.test_config.IMAGE_DIR, "*"))), 0)


    def test_transfer_2(self):
        """
        test_transfer_2 : if sqs queue is not working, end with no exception and
        returns the error message
        """
        # tempolarily delete sqs queue
        self.aws_sqs_client.delete_queue(QueueUrl=self.transfer_q_url)
        # expect no exception raises
        res = transfer_client.main()
        # restore sqs queue
        self.aws_sqs_client.create_queue(QueueName=self.test_config.AWS_SQS_TRANSFER_QUEUE_NAME)

        self.assertEqual(len(res["message_list"]), 1)
        self.assertEqual(
            res["message_list"][0], messages.TRANSFER_FAIL_SQS_ERROR.format(
                self.test_config.AWS_SQS_ENDPOINT_URL, self.test_config.AWS_SQS_TRANSFER_QUEUE_NAME
            ),
        )


    def test_transfer_3(self):
        """
        test_transfer_3 : if sqs queue message has no message body,
        returns the error message
        """
        # no message sent to queue
        # expect no exception raises
        res = transfer_client.main()

        self.assertEqual(len(res["message_list"]), 1)
        self.assertEqual(
            res["message_list"][0], messages.TRANSFER_FAIL_NO_MESSAGE.format(
                self.test_config.AWS_SQS_ENDPOINT_URL, self.test_config.AWS_SQS_TRANSFER_QUEUE_NAME
            ),
        )


    def test_transfer_4(self):
        """
        test_transfer_4 : if cannot get all images from s3 bucket,
        returns the error message
        """
        # temporarily delete s3 bucket
        self.aws_s3_resource.Bucket(
            self.test_config.AWS_S3_BUCKET_NAME
        ).objects.all().delete()
        # delete bucket
        self.aws_s3_client.delete_bucket(Bucket=self.test_config.AWS_S3_BUCKET_NAME)

        # prepare message
        message = self.send_sqs_message_for_transfer()
        # expect no exception raises
        res = transfer_client.main()

        # restore s3 bucket
        self.aws_s3_client.create_bucket(Bucket=self.test_config.AWS_S3_BUCKET_NAME)


        self.assertEqual(len(res["message_list"]), 1)
        self.assertEqual(
            res["message_list"][0], messages.TRANSFER_FAIL_S3_DOWNLOAD_ERROR.format(
                os.path.basename(self.transfer),
                self.test_config.AWS_S3_ENDPOINT_URL, self.test_config.AWS_S3_BUCKET_NAME,
                [os.path.basename(self.content), os.path.basename(self.style)]
            ),
        )


    def test_transfer_4(self):
        """
        test_transfer_4 : if partially cannot get images from s3 bucket,
        returns both error message and success message
        """

        # prepare message
        message = self.send_sqs_message_for_transfer()
        message = self.send_sqs_message_for_transfer(content_list=["NotExist.png"], style_list=["NotExist.png"], transfer_list=["NotExist.png"])

        # partially upload images
        self.upload_image_to_s3(self.content)
        self.upload_image_to_s3(self.style)

        # expect no exception raises
        res = transfer_client.main()


        self.assertEqual(len(res["message_list"]), 2)
        print(res)

        transfer_path = os.path.join(self.base_dir, "transfer.png")
        self.aws_s3_client.download_file(
            Filename=transfer_path,
            Bucket=config.AWS_S3_BUCKET_NAME,
            Key=self.s3_prefix + os.path.basename(transfer_path),
        )
        image = Image.open(transfer_path)

        assert_messages = [
            messages.TRANSFER_SUCCESS.format(
                os.path.basename(transfer_path), image.size
            ),
            messages.TRANSFER_FAIL_S3_DOWNLOAD_ERROR.format(
                "NotExist.png",
                self.test_config.AWS_S3_ENDPOINT_URL, self.test_config.AWS_S3_BUCKET_NAME,
                ["NotExist.png", "NotExist.png"]
            ),
        ]

        self.assertSetEqual(
            set(res["message_list"]), set(assert_messages)
        )


