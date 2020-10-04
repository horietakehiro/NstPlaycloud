from django.test import TestCase
from django.core.files.images import ImageFile
from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from django.conf import settings

import os
import time
import boto3
import requests
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.file_detector import LocalFileDetector
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.keys import Keys
options = webdriver.ChromeOptions()

from playground.models import Image, Result
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
    delete_q_url = None
    transfer_q_url = None

    aws_lambda_client = None
    lambda_ok = "test_lambda_ok"
    lambda_ng = "test_lambda_ng"
    lambda_zipcode = os.path.join(
        os.path.dirname(__file__), "dummy_lambda.zip",
    )


    aws_apigw_client = None
    rest_api_id = None
    parent_id = None
    resource_id = None
    deployment_id = None
    lambda_url_ok = None
    lambda_url_ng = None



    login_user = None
    login_username = "nstpc-test-user"
    login_userpass = "nstpc-test-pass"

    @classmethod
    def setUpClass(cls):

        # create bucket for test
        cls.aws_s3_client = boto3.client("s3", endpoint_url=settings.AWS_S3_ENDPOINT_URL)
        cls.aws_s3_resource = boto3.resource("s3", endpoint_url=settings.AWS_S3_ENDPOINT_URL)
        cls.aws_s3_client.create_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)

        # create queue for test
        cls.aws_sqs_client = boto3.client("sqs", endpoint_url=settings.AWS_SQS_ENDPOINT_URL)
        res = cls.aws_sqs_client.create_queue(QueueName=settings.AWS_SQS_DELETE_QUEUE_NAME)
        cls.delete_q_url = res["QueueUrl"]

        res = cls.aws_sqs_client.create_queue(QueueName=settings.AWS_SQS_TRANSFER_QUEUE_NAME)
        cls.transfer_q_url = res["QueueUrl"]


        # create lambda and apigateway
        cls.aws_lambda_client = boto3.client("lambda", 
            endpoint_url=settings.AWS_APIGW_ENDPOINT_URL, 
            region_name=settings.AWS_REGION,
        )
        cls.aws_apigw_client = boto3.client("apigateway", 
            endpoint_url=settings.AWS_APIGW_ENDPOINT_URL, 
            region_name=settings.AWS_REGION,
        )
        # lambda
        with open(cls.lambda_zipcode, "rb") as code:
            data = code.read()
            # ok
            cls.aws_lambda_client.create_function(
                FunctionName=cls.lambda_ok,
                Runtime="python3.6",
                Role="dummy",
                Handler="dummy_lambda.lambda_handler_ok",
                Code={"ZipFile" : data}
            )
            # ng
            cls.aws_lambda_client.create_function(
                FunctionName=cls.lambda_ng,
                Runtime="python3.6",
                Role="dummy",
                Handler="dummy_lambda.lambda_handler_ng",
                Code={"ZipFile" : data}
            )

        # apigateway
        res = cls.aws_apigw_client.create_rest_api(name=settings.AWS_APIGW_RESTAPI_NAME)
        cls.rest_api_id = res["id"]
        res = cls.aws_apigw_client.get_resources(restApiId=cls.rest_api_id)
        cls.parent_id = res["items"][0]["id"] # root resource id (/)

        # ok
        res = cls.aws_apigw_client.create_resource(
            restApiId=cls.rest_api_id, 
            parentId=cls.parent_id, pathPart=settings.AWS_APIGW_MASKING_PATH
        )
        cls.resource_id = res["id"]
        res = cls.aws_apigw_client.put_method(
            restApiId=cls.rest_api_id, 
            resourceId=cls.resource_id, 
            httpMethod="POST", 
            authorizationType="None"
        )
        res = cls.aws_lambda_client.get_function(FunctionName=cls.lambda_ok)
        lambda_arn = res["Configuration"]["FunctionArn"]
        uri = f"arn:aws:apigateway:{settings.AWS_REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
        res = cls.aws_apigw_client.put_integration(
            restApiId=cls.rest_api_id, 
            resourceId=cls.resource_id, 
            httpMethod="POST", 
            type="AWS_PROXY", 
            integrationHttpMethod="POST",
            uri=uri
        )
        cls.lambda_url_ok = f"{settings.AWS_APIGW_ENDPOINT_URL}restapis/{cls.rest_api_id}/test/_user_request_/{settings.AWS_APIGW_MASKING_PATH}"


        # ng
        res = cls.aws_apigw_client.create_resource(
            restApiId=cls.rest_api_id, 
            parentId=cls.parent_id, pathPart=settings.AWS_APIGW_MASKING_PATH + "_ng"
        )
        cls.resource_id = res["id"]
        res = cls.aws_apigw_client.put_method(
            restApiId=cls.rest_api_id, 
            resourceId=cls.resource_id, 
            httpMethod="POST", 
            authorizationType="None"
        )
        res = cls.aws_lambda_client.get_function(FunctionName=cls.lambda_ng)
        lambda_arn = res["Configuration"]["FunctionArn"]
        uri = f"arn:aws:apigateway:{settings.AWS_REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
        res = cls.aws_apigw_client.put_integration(
            restApiId=cls.rest_api_id, 
            resourceId=cls.resource_id, 
            httpMethod="POST", 
            type="AWS_PROXY", 
            integrationHttpMethod="POST",
            uri=uri
        )
        cls.lambda_url_ng = f"{settings.AWS_APIGW_ENDPOINT_URL}restapis/{cls.rest_api_id}/test/_user_request_/{settings.AWS_APIGW_MASKING_PATH + '_ng'}"

        res = cls.aws_apigw_client.create_deployment(
            restApiId=cls.rest_api_id, 
            stageName="test",
        )
        cls.deployment_id = res["id"]

        return super().setUpClass()

    def setUp(self):
        self.login_user = User.objects.create_superuser(
            username=self.login_username,
            password=self.login_userpass,
        )
        self.client.force_login(self.login_user)


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

        # login
        self.driver.get(self.live_server_url)
        if self.driver.current_url.startswith(self.live_server_url + "/admin/login"):
            username = self.get_element("id", "id_username")
            username.send_keys(self.login_username)
            password = self.get_element("id", "id_password")
            password.send_keys(self.login_userpass)
            password.send_keys(Keys.ENTER)



    @classmethod
    def tearDownClass(cls):
        # delete all objects
        cls.aws_s3_resource.Bucket(
            settings.AWS_STORAGE_BUCKET_NAME
        ).objects.all().delete()
        # delete bucket
        cls.aws_s3_client.delete_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)

        # delete queue
        cls.aws_sqs_client.delete_queue(QueueUrl=cls.delete_q_url)
        cls.aws_sqs_client.delete_queue(QueueUrl=cls.transfer_q_url)

        # delete apigateway
        res = cls.aws_apigw_client.get_rest_apis()
        for item in res["items"]:
            if item["name"].startswith("test"):
                cls.aws_apigw_client.delete_rest_api(restApiId=item["id"])
        # delete functions
        res = cls.aws_lambda_client.list_functions()
        for function in res["Functions"]:
            if function["FunctionName"].startswith("test"):
                cls.aws_lambda_client.delete_function(FunctionName=function["FunctionName"])


        return super().tearDownClass()

    def tearDown(self):
        self.client.logout()

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


    def create_result_record(self, content_path=None, style_path=None):
        """
        return result object
        """
        c = self.content if content_path is None else content_path
        s = self.style if style_path is None else style_path

        content = self.create_image_record(c)
        style = self.create_image_record(s)

        transfer, _ = Image.create_transfer_image(content_id=content.id, style_id=style.id)
        resutl = Result.objects.create(transfer_id=transfer.id, content_id=content.id, style_id=style.id)

        return resutl
        




    def create_tmp_driver(self):
        driver = webdriver.Remote(
            command_executor='http://browser:4444/wd/hub',
            options=options,
        )
        driver.file_detector = LocalFileDetector()
        # login
        driver.get(self.live_server_url)
        if driver.current_url.startswith(self.live_server_url + "/admin/login"):
            username = self.get_element("id", "id_username", driver=driver)
            username.send_keys(self.login_username)
            password = self.get_element("id", "id_password", driver=driver)
            password.send_keys(self.login_userpass)
            password.send_keys(Keys.ENTER)

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

    # def create_dummy_function(self, code_zipfile=None):
    #     if code_zipfile is None:
    #         code_zipfile = os.path(os.path.dirname(__file__), "dummy_lambda.zip")
        
    #     with open(code_zipfile, "rb") as code:
    #         ret = self.aws_lambda_client.create_function(
    #             FunctionName=self.lambda_funcname,
    #             Runtime="python3.6",
    #             Role="dummy",
    #             Handler="dummy_lambda.lambda_handler",
    #             Code={"ZipFile" : code}
    #         )

    
    # def create_rest_api(self):
        
