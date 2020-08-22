from django.core.files.images import ImageFile
from django.conf import settings

import os
from unittest.mock import patch

from ..common.base import BaseTestCase

from playground.models import Image
from playground.forms import ImageForm, TransferForm
from playground import messages
from playground.storages import MediaStorage


class ImageFormTestCase(BaseTestCase):

    def test_is_valid_1(self):
        """
        return true and sucess message if image is valid
        """
        basename = os.path.basename(self.content)
        with open(self.content, "rb") as fp:
            image = ImageFile(fp, name=basename)
            form = ImageForm({}, {"image" : image})
            is_valid, msg = form.is_valid()

        self.assertListEqual(
            [is_valid, msg],
            [True, messages.UPLOAD_SUCCESS.format(basename)]
        )

    def test_is_valid_2(self):
        """
        return false and fail message if image is invalid
        """
        basename = os.path.basename(self.invalid)
        with open(self.invalid, "rb") as fp:
            image = ImageFile(fp, name=basename)
            form = ImageForm({}, {"image" : image})
            is_valid, msg = form.is_valid()

        self.assertListEqual(
            [is_valid, msg],
            [False, messages.UPLOAD_FAIL_INVALID.format(basename)]
        )

    @patch("playground.models.Image.objects.filter")
    def test_is_valid_3(self, filter_mock):
        """
        return false and fail message if image already exists
        """
        filter_mock.return_value = ["hoge"]
        
        basename = os.path.basename(self.content)
        with open(self.content, "rb") as fp:
            image = ImageFile(fp, name=basename)
            form = ImageForm({}, {"image" : image})
            is_valid, msg = form.is_valid()

        self.assertListEqual(
            [is_valid, msg],
            [False, messages.UPLOAD_FAIL_DUPLICATED.format(basename)]
        )
    
    def test_save_1(self):
        """
        return Image object if save(upload to s3) is succeeded
        """
        basename = os.path.basename(self.content)
        with open(self.content, "rb") as fp:
            image = ImageFile(fp, name=basename)
            form = ImageForm({}, {"image" : image})
            is_valid, msg = form.is_valid()
        
            image = form.save()
        self.assertEqual(
            image.basename, basename,
        )
    
    def test_save_2(self):
        """
        return None if save(upload to s3) is falied
        """

        basename = os.path.basename(self.content)
        with open(self.invalid, "rb") as fp:
            image = ImageFile(fp, name=basename)
            form = ImageForm({}, {"image" : image})
        
            image = form.save()

        self.assertIsNone(image)

class TransferFormTestCase(BaseTestCase):

    def test_init_1(self):
        """
        dynamically get choices field
        """
        pre_form = TransferForm()
        _ = self.create_image_record(self.content)
        post_form = TransferForm()

        self.assertListEqual(
            [
                len(pre_form.fields["content"].choices),
                len(post_form.fields["content"].choices),
            ],
            [0, 1]
        )
