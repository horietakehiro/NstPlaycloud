from ..common.base import BaseTestCase

from transfer.client import transfer_client
from transfer.common import config

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



