from ..common.base import BaseTestCase

import os
import json
from glob import glob
import boto3

from masking_creation import app

class MaskingCreationTestCase(BaseTestCase):

    def test_successfuccly_create_masked_images(self):

        event = self.load_event("null_endpoint.json")

        ret = app.lambda_handler(event, None)

        self.assertEqual(
            ret["statusCode"], 200
        )


        baseobjkey = "original/{}/transfer.png"
        ret = self.client.list_objects(Bucket=self.bucket)
        key_list = [content["Key"] for content in ret["Contents"]]

        self.assertSetEqual(
            set([
                self.content, self.transfer,
                baseobjkey.format("masked"),
                baseobjkey.format("masked_inv"),
                baseobjkey.format("binned"),
                baseobjkey.format("binned_inv"),
            ]),
            set(key_list)
        )


        self.assertEqual(
            len(glob(os.path.join(self.image_dir, "*.png"))), 0
        )
