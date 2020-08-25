from ..common.base import BaseTestCase

from unittest.mock import patch

import os
from django.core.files.images import ImageFile
from django.conf import settings

from playground.models import Image, Result
from playground import messages

class ImageModelTestCase(BaseTestCase):

    def test_thumbnail_1(self):
        """
        return the image's thumbnail path
        """
        with open(self.content, "rb") as fp:
            image = Image.objects.create()
            image.image.save(
                os.path.basename(self.content),
                ImageFile(fp),
            )

        self.assertEqual(
            image.thumbnail_url, image.image.url.replace("/original/", "/thumbnail/")
        )


    def test_send_delete_message_1(self):
        """
        send sqs queue a message(success)
        """

        with open(self.content, "rb") as fp:
            image = Image.objects.create(
                image=ImageFile(fp, name=os.path.basename(self.content)),
            )
        res = image.send_delete_message({})
        self.assertIsNone(res)


    @patch("playground.models.Image.sqs_client.send_message")
    def test_send_delete_message_2(self, send_mock):
        """
        if message sending fails due to endpoint error, raise warning message
        """
        send_mock.side_effect = Exception()

        with open(self.content, "rb") as fp:
            image = Image.objects.create(
                image=ImageFile(fp, name=os.path.basename(self.content)),
            )
        
        res = image.send_delete_message({})
        self.assertEqual(
            res, messages.DELETE_WARNING.format(
                settings.AWS_SQS_ENDPOINT_URL, settings.AWS_SQS_DELETE_QUEUE_NAME,
            )
        )

    def test_create_transfer_image_1(self):
        """
        create transfer image with content and style image
        """
        content = self.create_image_record(self.content)
        style = self.create_image_record(self.style)

        transfer, _ = Image.create_transfer_image(
            content_id=content.id, style_id=style.id
        )

        transfer_basename = os.path.basename(self.content).split(".")[0] + "_" +\
                            os.path.basename(self.style).split(".")[0] + ".png"
        self.assertEqual(transfer.basename, transfer_basename)

    def test_create_transfer_image_1(self):
        """
        if creation succeeded, returns messages
        """
        content = self.create_image_record(self.content)
        style = self.create_image_record(self.style)

        _, msg = Image.create_transfer_image(
            content_id=content.id, style_id=style.id
        )

        self.assertEqual(
            msg, messages.TRANSFER_SUCCESS.format(
                content.basename, style.basename,
            ),
        )


class ResultModelTestCase(BaseTestCase):

    def test_send_transfer_message_1(self):
        """
        if message sending succeeded, return None
        """
        content = self.create_image_record(self.content)
        style = self.create_image_record(self.style)

        transfer, _ = Image.create_transfer_image(
            content_id=content.id, style_id=style.id,
        )
        result = Result.objects.create(
            transfer_id=transfer.id, content_id=content.id, style_id=style.id,
        )

        res = result.send_transfer_message({})

        self.assertIsNone(res)

    @patch("playground.models.Result.sqs_client.send_message")
    def test_send_transfer_message_2(self, send_mock):
        """
        if message sending succeeded, return warn message
        """

        send_mock.side_effect = Exception()

        content = self.create_image_record(self.content)
        style = self.create_image_record(self.style)

        transfer, _ = Image.create_transfer_image(
            content_id=content.id, style_id=style.id,
        )
        result = Result.objects.create(
            transfer_id=transfer.id, content_id=content.id, style_id=style.id,
        )

        res = result.send_transfer_message({})

        self.assertEqual(
            res, messages.TRANSFER_WARNING.format(
                settings.AWS_SQS_ENDPOINT_URL, settings.AWS_SQS_TRANSFER_QUEUE_NAME,
            )
        )

