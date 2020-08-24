from ..common.base import BaseTestCase

import os
import json

from thumbnail_creation import app

class ThumbnailCreationTestCase(BaseTestCase):

    def test_successfully_create_thumbnail(self):
        event = self.load_event("success.json")
        event = self.overwrite_event(event)

        ret = app.lambda_handler(event, None)

        self.assertEqual(
            json.loads(ret)["status"], 200
        )

        ret = self.client.list_objects(Bucket=self.bucket)
        key_list = [content["Key"] for content in ret["Contents"]]
        self.assertIn(
            self.objkey.replace("original/", "thumbnail/"), key_list
        )

        self.assertFalse(
            os.path.exists(
                os.path.join(self.image_dir, self.objkey.split("/")[-1])
            )
        )