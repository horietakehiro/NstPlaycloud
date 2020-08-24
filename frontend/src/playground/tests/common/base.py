from django.test import TestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.files.images import ImageFile

from django.conf import settings

import os
import time
import boto3
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.file_detector import LocalFileDetector
from selenium.webdriver.support.select import Select
options = webdriver.ChromeOptions()

from playground.models import Image
from playground import messages

class BaseTestCase(StaticLiveServerTestCase):
    base_dir = os.path.join(os.path.dirname(__file__), "..", "test_datas")
    content = os.path.join(base_dir, "content.png")
    style = os.path.join(base_dir, "style.png")
    invalid = os.path.join(base_dir, "invalid.png")


    host = '0.0.0.0'
    driver = None
    aws_s3_client = None
    aws_s3_resource = None
    aws_sqs_client = None
    q_url = None

    @classmethod
    def setUpClass(cls):
        # create bucket for test
        cls.aws_s3_client = boto3.client("s3", endpoint_url=settings.AWS_S3_ENDPOINT_URL)
        cls.aws_s3_resource = boto3.resource("s3", endpoint_url=settings.AWS_S3_ENDPOINT_URL)
        cls.aws_s3_client.create_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)

        # create queue for test
        cls.aws_sqs_client = boto3.client("sqs", endpoint_url=settings.AWS_SQS_ENDPOINT_URL)
        res = cls.aws_sqs_client.create_queue(QueueName=settings.AWS_SQS_QUEUE_NAME)
        cls.q_url = res["QueueUrl"]

        return super().setUpClass()

    def setUp(self):
        if str(self.host) in self.live_server_url:
            self.live_server_url = self.live_server_url.replace(
                str(self.host), os.environ.get('HOSTNAME'),
            )
        return super().setUp()

    def setUp_driver(self):
        if self.driver is not None:
            self.driver.quit()
        self.driver = webdriver.Remote(
            command_executor='http://browser:4444/wd/hub',
            options=options,
        )
        self.driver.file_detector = LocalFileDetector()

    @classmethod
    def tearDownClass(cls):
        # delete all objects
        cls.aws_s3_resource.Bucket(
            settings.AWS_STORAGE_BUCKET_NAME
        ).objects.all().delete()
        # delete bucket
        cls.aws_s3_client.delete_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)

        # delete queue
        cls.aws_sqs_client.delete_queue(QueueUrl=cls.q_url)


        return super().tearDownClass()

    def tearDown(self):
        # delete all objects
        self.aws_s3_resource.Bucket(
            settings.AWS_STORAGE_BUCKET_NAME
        ).objects.all().delete()

        if self.driver is not None:
            self.driver.quit()
        return super().tearDown()


    def get_element(self, kind, target, single=True, driver=None):
        max_wait = 5
        start = time.time()

        find_method = "self.driver" if driver is None else "driver"

        if single:
            find_method += f".find_element_by_{kind}('{target}')"
        else:
            find_method += f".find_elements_by_{kind}('{target}')"
        
        while True:
            try:
                element = eval(find_method)
                return element
            except NoSuchElementException as ex:
                if time.time() - start > max_wait:
                    raise ex
                else:
                    time.sleep(0.5)
            except Exception as ex:
                raise ex        

    def upload_image(self, image_path):
        if self.driver.title != "NstPlayground":
            self.driver.get(self.live_server_url)

        upload_box = self.get_element(kind='id' ,target='id_image')
        upload_box.send_keys(image_path)
        submit = self.get_element(kind='id' ,target='submit')
        submit.click()

    def delete_image(self):
        if self.driver.title != "NstPlayground":
            self.driver.get(self.live_server_url)
        delete = self.get_element("class_name", "Delete")
        delete.click()
    
    def create_image_record(self, image_path):
        """
        return Image object createed
        """
        with open(image_path, "rb") as fp:
            image = Image.objects.create(
                image=ImageFile(fp, name=os.path.basename(image_path))
            )
        return image

    def create_tmp_driver(self):
        driver = webdriver.Remote(
            command_executor='http://browser:4444/wd/hub',
            options=options,
        )
        driver.file_detector = LocalFileDetector()
        return driver


    def exec_transfer(self, content_path, style_path):
        # open the page
        self.driver.get(self.live_server_url)
        h2 = self.get_element("tag_name" ,"h2")        
        self.assertEqual(h2.text, "ImageList")

        # upload content and style image
        self.upload_image(content_path)
        message_list = self.get_element("class_name", "messages", single=False)
        self.assertIn(
            messages.UPLOAD_SUCCESS.format(os.path.basename(content_path)),
            [m.text for m in message_list],
        )
        self.upload_image(style_path)
        message_list = self.get_element("class_name", "messages", single=False)
        self.assertIn(
            messages.UPLOAD_SUCCESS.format(os.path.basename(style_path)),
            [m.text for m in message_list],
        )

        # select two image for transfer
        content = self.get_element("id", "id_content")
        style = self.get_element("id", "id_style")

        Select(content).select_by_visible_text(os.path.basename(content_path))
        Select(style).select_by_visible_text(os.path.basename(style_path))
        submit = self.get_element("id", "transfer_submit")
        submit.click()

        message_list = self.get_element("class_name", "messages", single=False)
        self.assertIn(
            messages.TRANSFER_SUCCESS.format(
                os.path.basename(content_path),
                os.path.basename(style_path),
            ),
            [m.text for m in message_list],
        )
