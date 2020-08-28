from ..common.base import BaseTestCase

from app import lambda_handler

class ImageDeletionTestCase(BaseTestCase):

    def test_image_deletion_1(self):
        """
        test_image_deletion_1 : delete all images at s3 bucket specified in sqs queue message 
        """
        # upload images
        self.upload_images(self.image_path_1)
        self.upload_images(self.image_path_2)
        # make sure that images are uploaded at s3 bucket
        image_list = self.aws_s3_client.list_objects(Bucket=self.bucket)
        self.assertEqual(
            len(image_list["Contents"]), 20
        )


        # load message
        event = self.load_event("single-record.json")

        ret = lambda_handler(event, context=None)

        # check images at s3 bucket are all deleted
        image_list = self.aws_s3_client.list_objects(Bucket=self.bucket)
        self.assertEqual(ret["status"], 200)
        with self.assertRaises(KeyError):
            _ = image_list["Contents"]



    def test_image_deletion_2(self):
        """
        test_image_deletion_2 : delete all images at s3 bucket specified in sqs queue message
        sqs message may contain multiple records
        """
        # upload images
        self.upload_images(self.image_path_1)
        self.upload_images(self.image_path_2)
        # make sure that images are uploaded at s3 bucket
        image_list = self.aws_s3_client.list_objects(Bucket=self.bucket)
        self.assertEqual(
            len(image_list["Contents"]), 20
        )


        # load message
        event = self.load_event("multiple-records.json")

        ret = lambda_handler(event, context=None)

        # check images at s3 bucket are all deleted
        image_list = self.aws_s3_client.list_objects(Bucket=self.bucket)
        self.assertEqual(ret["status"], 200)
        with self.assertRaises(KeyError):
            _ = image_list["Contents"]




    def test_image_deletion_3(self):
        """
        test_image_deletion_3 : if cannot connect to s3 bucket,
        return 404 error
        """

        # temporarily delete s3 bucket
        bucket = self.aws_s3_resource.Bucket(self.bucket)
        bucket.objects.all().delete()
        bucket.delete()

        # load message
        event = self.load_event("single-record.json")

        ret = lambda_handler(event, context=None)

        # restore s3 bucket
        self.aws_s3_client.create_bucket(Bucket=self.bucket)

        self.assertEqual(ret["status"], 404)


