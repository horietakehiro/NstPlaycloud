from ..common.base import BaseTestCase
from django.conf import settings

import os
import time
import copy
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.select import Select

from playground import messages

class ImageListTestCase(BaseTestCase):

    def test_image_list_1(self):
        """
        open ImageList page, upload two images, and display them on the page
        """
        self.setUp_driver()

        # open the page
        self.driver.get(self.live_server_url)
        h2 = self.get_element("tag_name" ,"h2")
        self.assertEqual(h2.text, "ImageList")

        # upload images
        self.upload_image(self.content)
        message_list = self.get_element("class_name", "messages", single=False)
        self.assertIn(
            messages.UPLOAD_SUCCESS.format(os.path.basename(self.content)),
            [m.text for m in message_list],
        )
        self.upload_image(self.style)
        message_list = self.get_element("class_name", "messages", single=False)
        self.assertIn(
            messages.UPLOAD_SUCCESS.format(os.path.basename(self.style)),
            [m.text for m in message_list],
        )


        image_list = self.get_element("class_name", "ImageName", single=False)

        self.assertSetEqual(
            set([image.text for image in image_list]),
            set([
                os.path.basename(self.content),
                os.path.basename(self.style),
            ])
        )


    def test_image_list_2(self):
        """
        open ImageList page, try uploading invalid image, and upload fails.
        """
        self.setUp_driver()

        # open the page
        self.driver.get(self.live_server_url)
        h2 = self.get_element("tag_name" ,"h2")        
        self.assertEqual(h2.text, "ImageList")

        # upload invalid images
        self.upload_image(self.invalid)
        message_list = self.get_element("class_name", "messages", single=False)
        self.assertIn(
            messages.UPLOAD_FAIL_INVALID.format(os.path.basename(self.invalid)),
            [m.text for m in message_list],
        )

        image_list = self.get_element("class_name", "ImageName", single=False)

        self.assertEqual(len(image_list), 0)


    def test_image_list_3(self):
        """
        open ImageList page, try uploading duplicated image, and upload fails.
        """
        self.setUp_driver()

        # open the page
        self.driver.get(self.live_server_url)
        h2 = self.get_element("tag_name" ,"h2")        
        self.assertEqual(h2.text, "ImageList")

        # upload valid image
        self.upload_image(self.content)
        message_list = self.get_element("class_name", "messages", single=False)
        self.assertIn(
            messages.UPLOAD_SUCCESS.format(os.path.basename(self.content)),
            [m.text for m in message_list],
        )
        # upload duplicated image
        self.upload_image(self.content)
        message_list = self.get_element("class_name", "messages", single=False)
        self.assertIn(
            messages.UPLOAD_FAIL_DUPLICATED.format(os.path.basename(self.content)),
            [m.text for m in message_list],
        )

        image_list = self.get_element("class_name", "ImageName", single=False)

        self.assertEqual(len(image_list), 1)


    def test_image_list_4(self):
        """
        open ImageList page, if s3 is not working, upload fails.
        """
        self.setUp_driver()

        # tempolarily delete bucket
        self.aws_s3_resource.Bucket(
            "nstpc-test"
        ).objects.all().delete()
        self.aws_s3_resource.Bucket(
            "nstpc-test"
        ).delete()
        # self.aws_s3_client.delete_bucket(Bucket="nstpc-test")


        # open the page
        self.driver.get(self.live_server_url)
        h2 = self.get_element("tag_name" ,"h2")        
        self.assertEqual(h2.text, "ImageList")

        # upload valid image
        self.upload_image(self.content)
        message_list = self.get_element("class_name", "messages", single=False)
        # recreate bucket
        self.aws_s3_client.create_bucket(Bucket="nstpc-test")

        self.assertIn(
            messages.UPLOAD_FAIL_S3ERROR,
            [m.text for m in message_list],
        )


        image_list = self.get_element("class_name", "ImageName", single=False)

        self.assertEqual(len(image_list), 0)


    def test_image_list_5(self):
        """
        open ImageList page, upload image, and delete it
        """
        self.setUp_driver()
        # open the page
        self.driver.get(self.live_server_url)
        h2 = self.get_element("tag_name" ,"h2")        
        self.assertEqual(h2.text, "ImageList")

        # upload images
        self.upload_image(self.content)
        message_list = self.get_element("class_name", "messages", single=False)
        self.assertIn(
            messages.UPLOAD_SUCCESS.format(os.path.basename(self.content)),
            [m.text for m in message_list],
        )

        # delete image
        self.delete_image()
        message_list = self.get_element("class_name", "messages", single=False)
        self.assertIn(
            messages.DELETE_SUCCESS.format(os.path.basename(self.content)),
            [m.text for m in message_list],
        )
        image_list = self.get_element("class_name", "ImageName", single=False)
        self.assertEqual(len(image_list), 0)


    def test_image_list_6(self):
        """
        open ImageList page, upload image, and try deleting it twice
        """
        self.setUp_driver()
        # open the page
        self.driver.get(self.live_server_url)
        h2 = self.get_element("tag_name" ,"h2")        
        self.assertEqual(h2.text, "ImageList")

        # upload images
        self.upload_image(self.content)
        message_list = self.get_element("class_name", "messages", single=False)
        self.assertIn(
            messages.UPLOAD_SUCCESS.format(os.path.basename(self.content)),
            [m.text for m in message_list],
        )

        # store image's id
        action = self.get_element("id", "delete")
        image_id = action.get_attribute("action").split("/")[-1]

        
        # delete image twice
        driver = self.create_tmp_driver()
        driver.get(self.live_server_url)
        delete = self.get_element("class_name", "Delete", driver=driver)
        delete.click()
        driver.quit()

        delete = self.get_element("class_name", "Delete")
        delete.click()

        message_list = self.get_element("class_name", "messages", single=False)
        self.assertIn(
            messages.DELETE_FAIL_NOTEXISTS.format(image_id),
            [m.text for m in message_list],
        )

    def test_image_list_7(self):
        """
        open ImageList page, upload image, and try deleting it with get method
        """
        self.setUp_driver()
        # open the page
        self.driver.get(self.live_server_url)
        h2 = self.get_element("tag_name" ,"h2")        
        self.assertEqual(h2.text, "ImageList")

        # upload images
        self.upload_image(self.content)
        message_list = self.get_element("class_name", "messages", single=False)
        self.assertIn(
            messages.UPLOAD_SUCCESS.format(os.path.basename(self.content)),
            [m.text for m in message_list],
        )
        
        
        action = self.get_element("id", "delete")
        url = action.get_attribute("action")
        self.driver.get(url)

        message_list = self.get_element("class_name", "messages", single=False)
        self.assertIn(
            messages.DELETE_FAIL_INVALID_METHOD,
            [m.text for m in message_list],
        )


    def test_image_list_8(self):
        """
        open ImageList page, upload image, and delte it.
        image file delete request send sqs
        """
        self.setUp_driver()
        # open the page
        self.driver.get(self.live_server_url)
        h2 = self.get_element("tag_name" ,"h2")        
        self.assertEqual(h2.text, "ImageList")

        # upload images
        self.upload_image(self.content)
        message_list = self.get_element("class_name", "messages", single=False)
        self.assertIn(
            messages.UPLOAD_SUCCESS.format(os.path.basename(self.content)),
            [m.text for m in message_list],
        )

        # delete image
        self.delete_image()
        message_list = self.get_element("class_name", "messages", single=False)
        self.assertIn(
            messages.DELETE_SUCCESS.format(os.path.basename(self.content)),
            [m.text for m in message_list],
        )
        image_list = self.get_element("class_name", "ImageName", single=False)
        self.assertEqual(len(image_list), 0)

        # get sqs message
        message = self.aws_sqs_client.receive_message(QueueUrl=self.delete_q_url)        
        self.assertIn(
            os.path.basename(self.content),
            message["Messages"][0]["Body"],
        )


    def test_image_list_9(self):
        """
        open ImageList page, upload image, and delte it.
        raise warn message if sqs not working.
        """
        self.setUp_driver()
        # open the page
        self.driver.get(self.live_server_url)
        h2 = self.get_element("tag_name" ,"h2")        
        self.assertEqual(h2.text, "ImageList")

        # upload images
        self.upload_image(self.content)
        message_list = self.get_element("class_name", "messages", single=False)
        self.assertIn(
            messages.UPLOAD_SUCCESS.format(os.path.basename(self.content)),
            [m.text for m in message_list],
        )

        # temporalily delete sqs queue
        self.aws_sqs_client.delete_queue(QueueUrl=self.delete_q_url)

        # delete image
        self.delete_image()

        # recreate sqs queue
        self.aws_sqs_client.create_queue(QueueName=settings.AWS_SQS_DELETE_QUEUE_NAME)

        message_list = self.get_element("class_name", "messages", single=False)
        self.assertIn(
            messages.DELETE_WARNING.format(settings.AWS_SQS_ENDPOINT_URL, settings.AWS_SQS_DELETE_QUEUE_NAME),
            [m.text.split("\n") for m in message_list][0],
        )
        image_list = self.get_element("class_name", "ImageName", single=False)
        self.assertEqual(len(image_list), 0)

    def test_image_list_10(self):
        """
        open ImageList page, upload two images, and transfer with them.
        after that, transit to Result page and display transfer results.
        """
        self.setUp_driver()
        self.exec_transfer(self.content, self.style)

        # transit to ResultList page
        self.driver.get(self.live_server_url + "/result_list/0/")
        image_list = self.get_element("class_name", "TransferName", single=False)
        self.assertEqual(len(image_list), 1)

        # check transfer request is sent to sqs queue
        message = self.aws_sqs_client.receive_message(QueueUrl=self.transfer_q_url)        
        self.assertIn(
            "transfer",
            message["Messages"][0]["Body"],
        )


    def test_image_list_11(self):
        """
        open ImageList page, upload two images, and transfer with get method.
        """
        self.setUp_driver()
        # open the page
        self.driver.get(self.live_server_url)
        h2 = self.get_element("tag_name" ,"h2")        
        self.assertEqual(h2.text, "ImageList")

        # upload content and style image
        self.upload_image(self.content)
        message_list = self.get_element("class_name", "messages", single=False)
        self.assertIn(
            messages.UPLOAD_SUCCESS.format(os.path.basename(self.content)),
            [m.text for m in message_list],
        )
        self.upload_image(self.style)
        message_list = self.get_element("class_name", "messages", single=False)
        self.assertIn(
            messages.UPLOAD_SUCCESS.format(os.path.basename(self.style)),
            [m.text for m in message_list],
        )

        self.driver.get(self.live_server_url + "/transfer")

        message_list = self.get_element("class_name", "messages", single=False)
        self.assertIn(
            messages.TRANSFER_FAIL_INVALID_METHOD,
            [m.text for m in message_list],
        )


    def test_image_list_12(self):
        """
        open ImageList page, upload two images, and transfer with them.
        if sqs queue is not working, also raise warning message
        """
        self.setUp_driver()
        # open the page
        self.driver.get(self.live_server_url)
        h2 = self.get_element("tag_name" ,"h2")        
        self.assertEqual(h2.text, "ImageList")

        # upload content and style image
        self.upload_image(self.content)
        message_list = self.get_element("class_name", "messages", single=False)
        self.assertIn(
            messages.UPLOAD_SUCCESS.format(os.path.basename(self.content)),
            [m.text for m in message_list],
        )
        self.upload_image(self.style)
        message_list = self.get_element("class_name", "messages", single=False)
        self.assertIn(
            messages.UPLOAD_SUCCESS.format(os.path.basename(self.style)),
            [m.text for m in message_list],
        )

        # temporalily delete sqs queue
        self.aws_sqs_client.delete_queue(QueueUrl=self.transfer_q_url)

        # select two image for transfer
        content = self.get_element("id", "id_content")
        style = self.get_element("id", "id_style")

        Select(content).select_by_visible_text(os.path.basename(self.content))
        Select(style).select_by_visible_text(os.path.basename(self.style))
        submit = self.get_element("id", "transfer_submit")
        submit.click()

        # recreate sqs queue
        self.aws_sqs_client.create_queue(QueueName=settings.AWS_SQS_TRANSFER_QUEUE_NAME)

        message_list = self.get_element("class_name", "messages", single=False)
        self.assertIn(
            messages.TRANSFER_WARNING.format(settings.AWS_SQS_ENDPOINT_URL, settings.AWS_SQS_TRANSFER_QUEUE_NAME),
            [m.text.split("\n") for m in message_list][0],
        )

    def test_image_list_13(self):
        """
        can transit to result_list page from image_list page
        """
        self.setUp_driver()

        self.driver.get(self.live_server_url)
        h2 = self.get_element("tag_name" ,"h2")
        self.assertEqual(h2.text, "ImageList")
        
        link = self.get_element("id", "result_list_link")
        link.click()
        h2 = self.get_element("tag_name" ,"h2")
        self.assertEqual(h2.text, "ResultList")

        
    