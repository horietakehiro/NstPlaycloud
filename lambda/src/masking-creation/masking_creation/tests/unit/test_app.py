from ..common.base import BaseTestCase

import os
import boto3

from masking_creation import app

class AppTestCase(BaseTestCase):

    def test_validate_and_get_parameter_empty_body(self):
        event = self.load_event("empty_body.json")
        params = app.get_params(event)

        self.assertDictEqual(
            params, {"statusCode" : 400, "body" : f"body is empty"}
        )


    def test_validate_and_get_parameter_null_body(self):
        event = self.load_event("null_body.json")
        params = app.get_params(event)

        self.assertDictEqual(
            params, {"statusCode" : 400, "body" : f"body is empty"}
        )

    def test_validate_and_get_parameter_invalid_body(self):
        event = self.load_event("invalid_body.json")
        params = app.get_params(event)

        self.assertDictEqual(
            params, {"statusCode" : 400, "body" : f"body : {event['body']} is invalid"}
        )

    def test_validate_and_get_parameter_null_bucket(self):
        event = self.load_event("null_bucket.json")
        params = app.get_params(event)

        self.assertDictEqual(
            params, {"statusCode" : 400, "body" : f"bucket is empty"}
        )

    def test_validate_and_get_parameter_null_content(self):
        event = self.load_event("null_content.json")
        params = app.get_params(event)

        self.assertDictEqual(
            params, {"statusCode" : 400, "body" : f"content is empty"}
        )

    def test_validate_and_get_parameter_null_transfer(self):
        event = self.load_event("null_transfer.json")
        params = app.get_params(event)

        self.assertDictEqual(
            params, {"statusCode" : 400, "body" : f"transfer is empty"}
        )


    def test_validate_and_get_parameter_null_endpoint(self):
        event = self.load_event("null_endpoint.json")

        params = app.get_params(event)

        self.assertDictEqual(
            params, 
            {
                "statusCode" :200, 
                "body" : "", 
                "s3_endpoint" : None, 
                "bucket" : self.bucket, 
                "content" : self.content,
                "transfer" : self.transfer,
            }
        )
    
    def test_validate_and_get_parameter_nonnull_endpoint(self):
        event = self.load_event("nonnull_endpoint.json")

        params = app.get_params(event)

        self.assertDictEqual(
            params, 
            {
                "statusCode" :200, 
                "body" : "", 
                "s3_endpoint" : "http://localhost/", 
                "bucket" : self.bucket, 
                "content" : self.content,
                "transfer" : self.transfer,
            }
        )

    def test_validate_and_get_parameter_invalid_endpoint(self):
        event = self.load_event("invalid_endpoint.json")

        params = app.get_params(event)

        self.assertDictEqual(
            params, {"statusCode" : 400, "body" : f"s3_endpoint : invalid_endpoint is invalid"}
        )
    def test_validate_and_get_parameter_keyerror_endpoint(self):
        event = self.load_event("keyerror_endpoint.json")

        params = app.get_params(event)

        self.assertDictEqual(
            params, {"statusCode" : 400, "body" : f"field : s3_endpoint does not exist"}
        )


    def test_validate_and_get_parameter_keyerror_bucket(self):
        event = self.load_event("keyerror_bucket.json")

        params = app.get_params(event)

        self.assertDictEqual(
            params, {"statusCode" : 400, "body" : f"field : bucket does not exist"}
        )

    def test_validate_and_get_parameter_keyerror_content(self):
        event = self.load_event("keyerror_content.json")

        params = app.get_params(event)

        self.assertDictEqual(
            params, {"statusCode" : 400, "body" : f"field : content does not exist"}
        )

    def test_validate_and_get_parameter_keyerror_transfer(self):
        event = self.load_event("keyerror_transfer.json")

        params = app.get_params(event)

        self.assertDictEqual(
            params, {"statusCode" : 400, "body" : f"field : transfer does not exist"}
        )


    def test_download_and_save_image_from_s3(self):

        ret = app.download_file(self.client, self.bucket, self.content, image_dir=self.image_dir)

        self.assertTrue(
            os.path.exists(os.path.join(
                self.image_dir, self.content.split("/")[-1]
            ))
        )

    def test_return_error_message_if_bucket_not_found(self):
        ret = app.download_file(self.client, "not-found-bucket", self.content, image_dir=self.image_dir)

        self.assertDictEqual(
            ret,
            {"statusCode" : 404, "body" : f"not-found-bucket/{self.content} is not found"},
        )

    def test_return_error_result_if_content_not_found(self):
        ret = app.download_file(self.client, self.bucket, "not-found-content", image_dir=self.image_dir)

        self.assertDictEqual(
            ret,
            {"statusCode" : 404, "body" : f"{self.bucket}/not-found-content is not found"},
        )

    def test_return_error_result_if_endpoint_cannot_connects_download(self):
        invalid_client = boto3.client("s3", endpoint_url="http://notfoundendpoint")
        ret = app.download_file(invalid_client, self.bucket, self.content, image_dir=self.image_dir)

        self.assertDictEqual(
            ret,
            {"statusCode" : 404, "body" : f"cannot connect to {str(invalid_client._endpoint)}"},
        )


    def test_mask_image_create_4new_images(self):
        ret = app.download_file(self.client, self.bucket, self.content, image_dir=self.image_dir)
        ret = app.download_file(self.client, self.bucket, self.transfer, image_dir=self.image_dir)

        ret = app.mask_image(self.content, self.transfer, self.image_dir)

        # base = os.path.join(self.image_dir, self.content.split("/")[-1])
        masked = os.path.join(self.image_dir, "masked_" + self.transfer.split("/")[-1])
        masked_inv = os.path.join(self.image_dir, "masked_inv_" + self.transfer.split("/")[-1])
        binned = os.path.join(self.image_dir, "binned_" + self.transfer.split("/")[-1])
        binned_inv = os.path.join(self.image_dir, "binned_inv_" + self.transfer.split("/")[-1])

        self.assertTrue(
            all([
                os.path.exists(masked),
                os.path.exists(masked_inv),
                os.path.exists(binned),
                os.path.exists(binned_inv),
            ])
        )


    def test_upload__image_to_s3(self):
        ret = app.download_file(self.client, self.bucket, self.content, image_dir=self.image_dir)
        ret = app.download_file(self.client, self.bucket, self.transfer, image_dir=self.image_dir)
        ret = app.mask_image(self.content, self.transfer, self.image_dir)

        ret = app.upload_files(self.client, self.bucket, self.transfer, self.image_dir)

        ret = self.client.list_objects(Bucket=self.bucket)
        key_list = [content["Key"] for content in ret["Contents"]]
        self.assertIn(
            self.content, key_list
        )

    def test_return_error_result_if_endpoint_cannot_connects_uploaed(self):
        ret = app.download_file(self.client, self.bucket, self.content, image_dir=self.image_dir)
        ret = app.download_file(self.client, self.bucket, self.transfer, image_dir=self.image_dir)
        ret = app.mask_image(self.content, self.transfer, self.image_dir)

        invalid_client = boto3.client("s3", endpoint_url="http://notfoundendpoint")
        ret = app.upload_files(invalid_client, self.bucket, self.transfer, self.image_dir)

        self.assertDictEqual(
            ret,
            {"statusCode" : 404, "body" : f"cannot connect to {str(invalid_client._endpoint)}"},
        )



