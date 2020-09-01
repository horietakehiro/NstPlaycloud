from ..common.base import BaseTestCase
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.files.images import ImageFile

import os

from unittest.mock import patch, Mock

from playground.models import Image
from playground import messages


class ImageListTestCase(BaseTestCase):


    def test_image_list_1(self):
        """
        image_list view returns image_list.html template
        """
        resp = self.client.get("/")
        self.assertTemplateUsed(resp, "playground/image_list.html")

    def test_image_list_2(self):
        """
        image_list view only accept get method
        """
        resp = self.client.post("/")
        self.assertEqual(
            resp.status_code, 405
        )



@patch("playground.forms.ImageForm.save")
@patch("playground.forms.ImageForm.is_valid")
class UploadTestCase(BaseTestCase):
    
    def test_upload_1(self, is_valid_mock, save_mock):
        """
        if upload succeeded, redirect to image_list
        """
        is_valid_mock.return_value = (True, "")
        
        with open(self.content, "rb") as fp:
            resp = self.client.post("/upload", data={"image" : fp})
        
        self.assertRedirects(resp, "/image_list/")

    def test_upload_2(self, is_valid_mock, save_mock):
        """
        image is saved if image is valid
        """
        is_valid_mock.return_value = (True, "")
        with open(self.content, "rb") as fp:
            resp = self.client.post("/upload", data={"image" : fp})
        
        self.assertListEqual(
            [is_valid_mock.call_count, save_mock.call_count],
            [1, 1],
        )

    def test_upload_3(self, is_valid_mock, save_mock):
        """
        image is not saved if image is invalid
        """
        is_valid_mock.return_value = (False, "")
        with open(self.invalid, "rb") as fp:
            resp = self.client.post("/upload", data={"image" : fp})
        
        self.assertEqual(save_mock.call_count, 0)

    def test_upload_4(self, is_valid_mock, save_mock):
        """
        image is not saved if s3 is not working
        """
        is_valid_mock.return_value = (True, "")
        save_mock.return_value = None, ""
        with open(self.content, "rb") as fp:
            resp = self.client.post("/upload", data={"image" : fp})
        
        self.assertEqual(Image.objects.count(), 0)

    def test_upload_5(self, is_valid_mock, save_mock):
        """
        upload view accept only POST method
        """
        resp = self.client.get("/upload")
        self.assertEqual(
            resp.status_code, 405
        )


# @patch("playground.models.Image.delete")
class DeleteTestCase(BaseTestCase):

    def test_delete_1(self):
        """
        if delete succeeds, redirect image_list view
        """
        image = self.create_image_record(self.content)

        resp = self.client.post("/delete/{}".format(image.id))
        self.assertRedirects(resp, "/image_list/")

    def test_delete_2(self):
        """
        delete view calls delete method of Image object
        """
        image = self.create_image_record(self.content)
        resp = self.client.post("/delete/{}".format(image.id))

        self.assertEqual(Image.objects.count(), 0)

    def test_delete_3(self):
        """
        delete view return error message if object does not exists
        """
        image_id = 99999
        resp = self.client.post("/delete/{}".format(image_id))

        self.assertRedirects(resp, "/image_list/")

    def test_delete_4(self):
        """
        delete view accepts only post method
        """
        image_id = 99999
        resp = self.client.get("/delete/{}".format(image_id))

        self.assertRedirects(resp, "/image_list/")


    @patch("playground.models.Image.send_delete_message")
    def test_delete_5(self, send_mock):
        """
        delete view also send message to sqs queue
        """
        send_mock.return_value = None
        image = self.create_image_record(self.content)
        resp = self.client.post("/delete/{}".format(image.id))

        self.assertEqual(send_mock.call_count, 1)

    @patch("playground.views.messages")
    @patch("playground.models.Image.send_delete_message")
    def test_delete_5(self, send_mock, message_mock):
        """
        if message sending to sqs fail, also raise warn message
        """
        send_mock.return_value = ""
        image = self.create_image_record(self.content)
        resp = self.client.post("/delete/{}".format(image.id))

        self.assertEqual(message_mock.add_message.call_count, 2)

@patch("playground.views.Result")
@patch("playground.views.Image")
@patch("playground.views.TransferForm")
class TransferTestCase(BaseTestCase):

    def test_transfer_1(self, form_mock, image_mock, result_mock):
        """
        if transfer request succeeded, redirect to image_list with messages
        """
        content = self.create_image_record(self.content)
        style = self.create_image_record(self.style)

        # mock configure
        image_mock.create_transfer_image.return_value = Mock(id=1), ""
        form_mock.configure_mock(
            cleaned_data={"content" : content.id, "style" : style.id}
        )

        resp = self.client.post("/transfer", data={
            "content" : content.id, "style" : style.id,
        })

        self.assertRedirects(resp, "/image_list/")

    def test_transfer_2(self, form_mock, image_mock, result_mock):
        """
        transfer view create image record for transfer
        """
        content = self.create_image_record(self.content)
        style = self.create_image_record(self.style)

        # mock configure
        image_mock.create_transfer_image.return_value = Mock(id=1), ""
        form_mock.is_valid.return_value = True
        form_mock.configure_mock(
            cleaned_data={"content" : content.id, "style" : style.id}
        )

        resp = self.client.post("/transfer", data={
            "content" : content.id, "style" : style.id,
        })

        self.assertEqual(
            image_mock.create_transfer_image.call_count, 1
        )

    def test_transfer_3(self, form_mock, image_mock, result_mock):
        """
        transfer view accepts only post method
        """
        resp = self.client.get("/transfer")
        self.assertRedirects(resp, "/image_list/")

    def test_transfer_4(self, form_mock, image_mock, result_mock):
        """
        if form validation fails, raise error message
        """
        form_mock.is_valid.return_value = False
        image_mock.create_transfer_image.return_value = Mock(id=1), ""

        resp = self.client.post("/transfer", data={})

        self.assertEqual(
            image_mock.call_count, 0
        )

    def test_transfer_5(self, form_mock, image_mock, result_mock):
        """
        if transfer image creation succeeded, create result record
        """
        content = self.create_image_record(self.content)
        style = self.create_image_record(self.style)

        # mock configure
        image_mock.create_transfer_image.return_value = Mock(id=1), ""
        form_mock.configure_mock(
            cleaned_data={"content" : content.id, "style" : style.id}
        )
        resp = self.client.post("/transfer", data={
            "content" : content.id, "style" : style.id,
        })
        
        self.assertEqual(result_mock.objects.create.call_count, 1)

    def test_transfer_6(self, form_mock, image_mock, result_mock):
        """
        if result record created, send sqs massges for transfer
        """
        content = self.create_image_record(self.content)
        style = self.create_image_record(self.style)

        # mock configure
        image_mock.create_transfer_image.return_value = Mock(id=1), ""
        mock = Mock(**{"send_transfer_message.return_value" : None})
        result_mock.objects.create.return_value = mock
        form_mock.configure_mock(
            cleaned_data={"content" : content.id, "style" : style.id}
        )
        resp = self.client.post("/transfer", data={
            "content" : content.id, "style" : style.id,
        })

        self.assertEqual(
            mock.send_transfer_message.call_count, 1
        )


    @patch("playground.views.messages")
    def test_transfer_7(self, message_mock, form_mock, image_mock, result_mock):
        """
        if message sending fails, also raise warning message
        """
        content = self.create_image_record(self.content)
        style = self.create_image_record(self.style)

        # mock configure
        form_mock.configure_mock(
            cleaned_data={"content" : content.id, "style" : style.id}
        )
        image_mock.create_transfer_image.return_value = Mock(id=1), ""
        mock = Mock(**{"send_transfer_message.return_value" : ""})
        result_mock.objects.create.return_value = mock


        resp = self.client.post("/transfer", data={
            "content" : content.id, "style" : style.id,
        })
        self.assertEqual(message_mock.add_message.call_count, 2)


class ResultListTestCase(BaseTestCase):

    def test_result_list_1(self):
        """
        result_list returns result_list.html
        """
        resp = self.client.get("/result_list/0/")
        self.assertTemplateUsed(resp, "playground/result_list.html")

    def test_result_list_2(self):
        """
        result_list view only accept get method
        """
        resp = self.client.post("/result_list/0/")
        self.assertEqual(
            resp.status_code, 405
        )


    def test_result_list_3(self):
        """
        if image_id is specified, result_list view also disply result_list related to the image
        """
        # create transfer image
        content = self.create_image_record(self.content)
        style = self.create_image_record(self.style)
        self.client.post("/transfer", data={"content" : content.id, "style" : style.id})

        resp = self.client.get("/result_list/" + str(content.id) + "/")

        self.assertTemplateUsed(resp, "playground/result_list.html")


