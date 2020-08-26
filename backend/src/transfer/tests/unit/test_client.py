from ..common.base import BaseTestCase
from unittest.mock import patch, Mock

import os
import pathlib

from transfer.client import transfer_client
from transfer.common import config

@patch("transfer.client.transfer_client.put_image_to_s3")
@patch("transfer.client.transfer_client.call_engine")
@patch("transfer.client.transfer_client.preprocess_image")
@patch("transfer.client.transfer_client.get_images_from_s3")
@patch("transfer.client.transfer_client.receive_sqs_message")
class MainTestCase(BaseTestCase):

    def test_main_1(self, sqs_mock, s3_get_mock, image_mock, engine_mock, s3_put_mock):
        """
        test_main_1 : main function receive sqs message, get images from s3, 
        preprocess image, call engine. 
        """
        sqs_mock.return_value = {}
        s3_get_mock.return_value = "", "", ""
        image_mock.return_value = None, None, None
        engine_mock.return_value = Mock(shape=[1, 512, 512, 3])
        s3_put_mock.return_value = None


        res = transfer_client.main()

        self.assertListEqual(
            [
                sqs_mock.call_count, 
                s3_get_mock.call_count, 
                image_mock.call_count, 
                engine_mock.call_count,
                s3_put_mock.call_count,
            ],
            [1, 1, 2, 1, 1]
        )


@patch("transfer.client.transfer_client.boto3")
class ReceiveMEssageTestCase(BaseTestCase):

    sqs_return_message = {
        'Messages': [
            {
                'Body': '{}',
            },
        ]
    }

    sqs_return_queue = {
        'QueueUrl': ''
    }

    def test_receive_sqs_message_1(self, boto_mock):
        """
        test_receive_sqs_message_1 : receive message from sqs
        """
        mock = Mock(
            **{
                "get_queue_url.return_value" :self.sqs_return_queue,
                "receive_message.return_value" :self.sqs_return_message,
            }
        )
        boto_mock.client.return_value = mock

        message = transfer_client.receive_sqs_message(config=self.test_config)

        self.assertListEqual(
            [mock.get_queue_url.call_count, mock.receive_message.call_count],
            [1, 1],
        )


    def test_receive_sqs_message_2(self, boto_mock):
        """
        test_receive_sqs_message_2 : receive message from sqs and return the body as dict
        """
        mock = Mock(
            **{
                "get_queue_url.return_value" :self.sqs_return_queue,
                "receive_message.return_value" :self.sqs_return_message,
            }
        )
        boto_mock.client.return_value = mock

        message = transfer_client.receive_sqs_message(config=self.test_config)

        self.assertTrue(isinstance(message, dict))


@patch("transfer.client.transfer_client.boto3")
class GetImageTestCase(BaseTestCase):

    message = {
        "request_type" : "transfer",
        "request_body" : {
            "transfer_list" : ["transfer.png"],
            "content_list" : ["content.png"],
            "style_list" : ["style.png"],

            "key_prefix" : "media/original/raw/" ,
            "bucket" : BaseTestCase.test_config.AWS_S3_BUCKET_NAME,
            "s3_endpoint" : BaseTestCase.test_config.AWS_S3_ENDPOINT_URL,
        }
    }

    def test_get_images_from_s3_1(self, boto_mock):
        """
        test_get_images_from_s3_1 : download content and style images from s3
        """
        mock = Mock(
            **{
                "download_file.return_value" : {},
            }
        )
        boto_mock.client.return_value = mock

        _ = transfer_client.get_images_from_s3(self.test_config, self.message)

        self.assertEqual(mock.download_file.call_count, 2)


    def test_get_images_from_s3_2(self, boto_mock):
        """
        test_get_images_from_s3_2 : downloaded images are saved as local file
        """
        # def side_effect(*arg, Filename, Bucket, Key):
        def side_effect(Filename, Bucket, Key, *args, **kwargs):
            # print("hoge")
            pathlib.Path(Filename).touch()

        mock = Mock(
            **{
                "download_file.return_value" : {},
                "download_file.side_effect" : side_effect,
            }
        )
        boto_mock.client.return_value = mock
        c, s, t = transfer_client.get_images_from_s3(self.test_config, self.message)

        self.assertListEqual(
            [os.path.exists(c), os.path.exists(s), os.path.exists(t)],
            [True, True, False]
        )

