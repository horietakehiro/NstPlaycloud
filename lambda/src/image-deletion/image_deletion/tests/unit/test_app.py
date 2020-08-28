import unittest
from unittest.mock import patch, Mock
from ..common.base import BaseTestCase

import json

import app


@patch("app.delete_images")
class AppTestCase(BaseTestCase):

    def test_lambda_handler_1(self, delete_mock):
        """
        test_lambda_handler_1 : if image deletion succeeded, returnn status code 200
        """
        event = self.load_event("single-record.json")
        
        delete_mock.return_value = None
        ret = app.lambda_handler(event, context=None)

        self.assertEqual(ret["status"], 200)


    def test_lambda_handler_2(self, delete_mock):
        """
        test_lambda_handler_2 : message may contain multiple records
        """
        event = self.load_event("multiple-records.json")
        
        delete_mock.return_value = None
        ret = app.lambda_handler(event, context=None)

        self.assertEqual(delete_mock.call_count, 2)


    def test_lambda_handler_3(self, delete_mock):
        """
        test_lambda_handler_3 : if deletion fails, return 404 and error message
        """
        event = self.load_event("single-record.json")
        
        delete_mock.return_value = ""
        ret = app.lambda_handler(event, context=None)

        self.assertEqual(ret["status"], 404)


@patch("app.boto3")
class DeleteImagesTestCase(BaseTestCase):

    def test_delete_images_1(self, boto_mock):
        """
        test_delete_images_1 : delete all images according to sqs message
        if succeede, return None
        """
        event = self.load_event("single-record.json")
        message = json.loads(event["Records"][0]["body"])

        mock = Mock(**{"delete_objects.return_value" : {}})
        boto_mock.client.return_value = mock
        
        ret = app.delete_images(message)

        self.assertEqual(ret, None)


    def test_delete_images_2(self, boto_mock):
        """
        test_delete_images_2 : delete all images according to sqs message.
        this calls boto method once
        """
        event = self.load_event("single-record.json")
        message = json.loads(event["Records"][0]["body"])

        mock = Mock(**{"delete_objects.return_value" : {}})
        boto_mock.client.return_value = mock
        
        ret = app.delete_images(message)

        self.assertEqual(
            mock.delete_objects.call_count, 1
        )



    def test_delete_images_3(self, boto_mock):
        """
        test_delete_images_3 : if cannot connect to s3 bucket,
        return error message
        """
        event = self.load_event("single-record.json")
        message = json.loads(event["Records"][0]["body"])

        mock = Mock(**{"delete_objects.side_effect" : Exception})
        boto_mock.client.return_value = mock
        
        ret = app.delete_images(message)

        self.assertTrue(isinstance(ret, str))

