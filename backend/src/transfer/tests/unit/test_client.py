from ..common.base import BaseTestCase
from unittest.mock import patch, Mock

import os
import pathlib
import numpy as np

from transfer.client import transfer_client
from transfer.common import config, messages, exceptions

@patch("transfer.client.transfer_client.put_image_to_s3")
@patch("transfer.client.transfer_client.postprocess_image")
@patch("transfer.client.transfer_client.call_engine")
@patch("transfer.client.transfer_client.preprocess_image")
@patch("transfer.client.transfer_client.get_images_from_s3")
@patch("transfer.client.transfer_client.receive_sqs_message")
class MainTestCase(BaseTestCase):

    message_list = [
        {
            "request_type" : "transfer",
            "request_body" : {
                "transfer_list" : ["transfer.png", "transfer.png"],
                "content_list" : ["content.png", "content.png"],
                "style_list" : ["style.png", "style.png"],

                "key_prefix" : "media/original/raw/" ,
                "bucket" : BaseTestCase.test_config.AWS_S3_BUCKET_NAME,
                "s3_endpoint" : BaseTestCase.test_config.AWS_S3_ENDPOINT_URL,
            }
        },
        {
            "request_type" : "transfer",
            "request_body" : {
                "transfer_list" : ["transfer.png", "transfer.png"],
                "content_list" : ["content.png", "content.png"],
                "style_list" : ["style.png", "style.png"],

                "key_prefix" : "media/original/raw/" ,
                "bucket" : BaseTestCase.test_config.AWS_S3_BUCKET_NAME,
                "s3_endpoint" : BaseTestCase.test_config.AWS_S3_ENDPOINT_URL,
            }
        }
    ]


    def test_main_1(self, sqs_mock, s3_get_mock, pre_image_mock, engine_mock, post_image_mock, s3_put_mock):
        """
        test_main_1 : success case.
        main function receive sqs message, get images from s3, 
        preprocess image, call engine, postprocess the resutl, and upload it to s3.
        Finally return the response.
        """

        sqs_mock.return_value = self.message_list
        s3_get_mock.return_value = [["c", "s", "t"], ["c", "s", "t"]]
        pre_image_mock.return_value = Mock(shape=[1, 512, 512, 3])
        engine_mock.return_value = Mock(shape=[1, 512, 512, 3])
        post_image_mock.return_value = "/mock/mock.mock"
        s3_put_mock.return_value = {}

        res = transfer_client.main()

        self.assertListEqual(
            [
                sqs_mock.call_count, 
                s3_get_mock.call_count, 
                pre_image_mock.call_count, 
                engine_mock.call_count,
                post_image_mock.call_count,
                s3_put_mock.call_count,
            ],
            [1, 2, 8, 4, 4, 4]
        )

    def test_main_2(self, sqs_mock, s3_get_mock, pre_image_mock, engine_mock, post_image_mock, s3_put_mock):
        """
        test_main_2 : fail case.
        if main function fails to receive message from sqs queue,
        return error message. 
        """
        sqs_mock.side_effect = exceptions.SQSConnectionError("", "")
        # s3_get_mock.return_value = "", "", ""
        # pre_image_mock.return_value = None, None, None
        # engine_mock.return_value = Mock(shape=[1, 512, 512, 3])
        # post_image_mock.return_value = "/mock/mock.mock"
        # s3_put_mock.return_value = None

        res = transfer_client.main()

        self.assertListEqual(
            [
                sqs_mock.call_count, 
                s3_get_mock.call_count, 
                pre_image_mock.call_count, 
                engine_mock.call_count,
                post_image_mock.call_count,
                s3_put_mock.call_count,
            ],
            [1, 0, 0, 0, 0, 0]
        )


    def test_main_3(self, sqs_mock, s3_get_mock, pre_image_mock, engine_mock, post_image_mock, s3_put_mock):
        """
        test_main_3 : fail case.
        if main function receive no message from sqs queue,
        return error message. 
        """
        sqs_mock.side_effect = exceptions.SQSNoMessageError("", "")
        # s3_get_mock.return_value = "", "", ""
        # pre_image_mock.return_value = None, None, None
        # engine_mock.return_value = Mock(shape=[1, 512, 512, 3])
        # post_image_mock.return_value = "/mock/mock.mock"
        # s3_put_mock.return_value = None

        res = transfer_client.main()

        self.assertListEqual(
            [
                sqs_mock.call_count, 
                s3_get_mock.call_count, 
                pre_image_mock.call_count, 
                engine_mock.call_count,
                post_image_mock.call_count,
                s3_put_mock.call_count,
            ],
            [1, 0, 0, 0, 0, 0]
        )


    def test_main_4(self, sqs_mock, s3_get_mock, pre_image_mock, engine_mock, post_image_mock, s3_put_mock):
        """
        test_main_4 : if main function fails to get all images from s3 bucket,
        return error message. 
        """
        message = self.transfer_queue_message
        message["request_body"]["content_list"] = ["mock"]
        message["request_body"]["style_list"] = ["mock"]
        sqs_mock.return_value = message
        s3_get_mock.side_effect = exceptions.S3DownloadError("", "", "", "", "")
        # pre_image_mock.return_value = None, None, None
        # engine_mock.return_value = Mock(shape=[1, 512, 512, 3])
        # post_image_mock.return_value = "/mock/mock.mock"
        # s3_put_mock.return_value = None


        res = transfer_client.main()

        self.assertListEqual(
            [
                sqs_mock.call_count, 
                s3_get_mock.call_count, 
                pre_image_mock.call_count, 
                engine_mock.call_count,
                post_image_mock.call_count,
                s3_put_mock.call_count,
            ],
            [1, 2, 0, 0, 0, 0]
        )



    def test_main_5(self, sqs_mock, s3_get_mock, pre_image_mock, engine_mock, post_image_mock, s3_put_mock):
        """
        test_main_5 : if main function fails to upload transfer resutl to s3 bucket,
        return error message. 
        """
        message = self.transfer_queue_message
        message["request_body"]["content_list"] = ["mock"]
        message["request_body"]["style_list"] = ["mock"]
        sqs_mock.return_value = message
        s3_get_mock.return_value = [["c", "s", "t"], ["c", "s", "t"]]
        pre_image_mock.return_value = Mock()
        engine_mock.return_value = Mock(shape=[1, 512, 512, 3])
        post_image_mock.return_value = "/mock/mock.mock"
        s3_put_mock.side_effect = exceptions.S3UploadError("", "", "")


        res = transfer_client.main()

        self.assertListEqual(
            [
                sqs_mock.call_count, 
                s3_get_mock.call_count, 
                pre_image_mock.call_count, 
                engine_mock.call_count,
                post_image_mock.call_count,
                s3_put_mock.call_count,
            ],
            [1, 2, 8, 4, 4, 4]
        )



@patch("transfer.client.transfer_client.boto3")
class ReceiveMEssageTestCase(BaseTestCase):

    sqs_return_message = {
        'Messages': [
            {
                'Body': '{}',
            },
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
        test_receive_sqs_message_1 : receive message from sqs and return the messages as list
        """
        mock = Mock(
            **{
                "get_queue_url.return_value" :self.sqs_return_queue,
                "receive_message.return_value" :self.sqs_return_message,
            }
        )
        boto_mock.client.return_value = mock
        message_list = transfer_client.receive_sqs_message(config=self.test_config)

        self.assertEqual(len(message_list), 2)


    def test_receive_sqs_message_2(self, boto_mock):
        """
        test_receive_sqs_message_2 : if cannot connect to sqs queue,
        raise Excaption with error message
        """
        mock = Mock(
            **{
                "get_queue_url.side_effect" : Exception,
            }
        )
        boto_mock.client.return_value = mock

        with self.assertRaises(exceptions.SQSConnectionError):
            message = transfer_client.receive_sqs_message(config=self.test_config)


    def test_receive_sqs_message_3(self, boto_mock):
        """
        test_receive_sqs_message_3 : if receive no messge from sqs queue,
        raise Excaption with error message
        """
        mock = Mock(
            **{
                "get_queue_url.return_value" : self.sqs_return_queue,
                "receive_message.return_value" : {},
            }
        )
        boto_mock.client.return_value = mock

        with self.assertRaises(exceptions.SQSNoMessageError):
            message = transfer_client.receive_sqs_message(config=self.test_config)


@patch("transfer.client.transfer_client.boto3")
class GetImageTestCase(BaseTestCase):

    message = {
        "request_type" : "transfer",
        "request_body" : {
            "transfer_list" : ["transfer.png", "transfer.png"],
            "content_list" : ["content.png", "content.png"],
            "style_list" : ["style.png", "style.png"],

            "key_prefix" : "media/original/raw/" ,
            "bucket" : BaseTestCase.test_config.AWS_S3_BUCKET_NAME,
            "s3_endpoint" : BaseTestCase.test_config.AWS_S3_ENDPOINT_URL,
        }
    }

    def test_get_images_from_s3_1(self, boto_mock):
        """
        test_get_images_from_s3_1 : download content and style images from s3.
        return the list of [[content_path, style_path, transfer_path], [...]]
        """
        mock = Mock(
            **{
                "download_file.return_value" : {},
            }
        )
        boto_mock.client.return_value = mock

        path_list = transfer_client.get_images_from_s3(self.test_config, self.message)

        self.assertTupleEqual(np.array(path_list).shape, (2,3))


    def test_get_images_from_s3_2(self, boto_mock):
        """
        test_get_images_from_s3_2 : if downloading image fails, raise Exception
        """
        mock = Mock(
            **{
                "download_file.side_effect" : Exception,
            }
        )
        boto_mock.client.return_value = mock
        with self.assertRaises(exceptions.S3DownloadError):
            path_list = transfer_client.get_images_from_s3(self.test_config, self.message)



# @patch("transfer.client.transfer_client")
class PreprocessTestCase(BaseTestCase):

    def test_preprocess_image_1(self):
        """
        test_preprocess_image_1 : returns the ndarray of image
        """
        new_size = self.calc_limited_shape(self.content)

        ret = transfer_client.preprocess_image(self.test_config, self.content)

        # shape
        self.assertTupleEqual(
            ret.shape, (1, *new_size, 3)
        )
        # dtype
        self.assertTrue(ret.dtype == np.float32)
        # scale 
        self.assertLessEqual(ret.max(axis=None), 1.)
        self.assertGreaterEqual(ret.min(axis=None), 0.)
        self.assertGreaterEqual(ret.max(axis=None), 0.1)


@patch("transfer.client.transfer_client.NstEngine")
class CallEngineTestCase(BaseTestCase):

    def test_call_engine_1(self, engine_mock):
        """
        test_call_engine_1 : call engine's fit with content and style and transfer(content) images
        """
        fit_mock = Mock(return_value = Mock())
        engine_mock.return_value = Mock(**{"fit" : fit_mock})
        
        content = transfer_client.preprocess_image(self.test_config, self.content)
        style = transfer_client.preprocess_image(self.test_config, self.style)
        
        ret = transfer_client.call_engine(self.test_config, content, style)

        _, kwargs = fit_mock.call_args
        np.testing.assert_array_equal(content, kwargs["content"])
        np.testing.assert_array_equal(style, kwargs["style"])
        np.testing.assert_array_equal(content, kwargs["content_org"])



class PostprocessTestCase(BaseTestCase):

    def test_postprocess_image_1(self):
        """
        test_postprocess_image_1 : save transfer result on local file
        """
        transfer = transfer_client.preprocess_image(self.test_config, self.transfer)
        transfer_path = os.path.join(self.test_config.IMAGE_DIR, "transfer.png")
        
        ret = transfer_client.postprocess_image(self.test_config, transfer, transfer_path)

        self.assertTrue(os.path.exists(ret))


@patch("transfer.client.transfer_client.boto3")
class PutImageTestCase(BaseTestCase):

    message = {
        "request_type" : "transfer",
        "request_body" : {
            "key_prefix" : "media/original/raw/" ,
            "bucket" : BaseTestCase.test_config.AWS_S3_BUCKET_NAME,
            "s3_endpoint" : BaseTestCase.test_config.AWS_S3_ENDPOINT_URL,
        }
    }

    def test_put_image_to_s3_1(self, boto_mock):
        """
        test_put_image_to_s3_1 : upload transfer image
        """

        mock = Mock(
            **{
                "upload_file.return_value" : {},
            }
        )
        boto_mock.client.return_value = mock
        transfer_path = os.path.join(self.test_config.IMAGE_DIR, "transfer.png")
        ret = transfer_client.put_image_to_s3(self.test_config, self.message, transfer_path)

        self.assertEqual(mock.upload_file.call_count, 1)



    def test_put_image_to_s3_2(self, boto_mock):
        """
        test_put_image_to_s3_2 : if uploading fails, return error message
        """

        mock = Mock(
            **{
                "upload_file.side_effect" : Exception,
            }
        )
        boto_mock.client.return_value = mock
        transfer_path = os.path.join(self.test_config.IMAGE_DIR, "transfer.png")
        with self.assertRaises(exceptions.S3UploadError):
            ret = transfer_client.put_image_to_s3(self.test_config, self.message, transfer_path)


