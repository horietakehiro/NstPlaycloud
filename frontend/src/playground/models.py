from django.db import models
from django.conf import settings
from django.core.files.images import ImageFile

from playground.storages import MediaStorage
from playground import messages

import os
import boto3
from botocore import client
import json


# Create your models here.
class Image(models.Model):
    image = models.ImageField(upload_to="original/raw/")

    sqs_client = boto3.client("sqs", endpoint_url=settings.AWS_SQS_ENDPOINT_URL)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.delete_queue_message = {
            "request_type" : "delete",
            "request_body" : {
                "basenames" : [
                    self.basename,
                ],
                "bucket" : settings.AWS_STORAGE_BUCKET_NAME,
                "s3_endpoint" : settings.AWS_S3_ENDPOINT_URL,
                "prefixes" : [
                    MediaStorage.location + "/" + "original/raw/",
                    MediaStorage.location + "/" + "original/masked/",
                    MediaStorage.location + "/" + "original/maskied_inv/",
                    MediaStorage.location + "/" + "original/binned/",
                    MediaStorage.location + "/" + "original/binned_inv/",
                    MediaStorage.location + "/" + "thumbnail/raw/",
                    MediaStorage.location + "/" + "thumbnail/masked/",
                    MediaStorage.location + "/" + "thumbnail/maskied_inv/",
                    MediaStorage.location + "/" + "thumbnail/binned/",
                    MediaStorage.location + "/" + "thumbnail/binned_inv/",
                ],
            }
        }

    @property
    def basename(self):
        return os.path.basename(self.image.name)

    @property
    def thumbnail_url(self):
        return self.image.url.replace("/original/", "/thumbnail/")


    def send_delete_message(self):
        """
        send sqs queue a request message to delete imgage files on s3
        """
        try:
            q_url = self.sqs_client.get_queue_url(QueueName=settings.AWS_SQS_QUEUE_NAME)

            res = self.sqs_client.send_message(
                QueueUrl=q_url["QueueUrl"], 
                MessageBody=json.dumps(self.delete_queue_message),
            )

            return None
        
        except:
            return messages.DELETE_WARNING.format(
                settings.AWS_SQS_ENDPOINT_URL, settings.AWS_SQS_QUEUE_NAME,
            )

    @classmethod
    def create_transfer_image(cls, content_id, style_id):
        """
        transfer's name is {content's basename}_{style's basename}.png
        transfer's (dummy) image is statics file : "processing.png"
        
        if creation succeeded, return (image object, success message)
        if creation fails, return (None, fail message)
        """
        # form validation guarantees that content and style images are certainly exist.
        content = cls.objects.get(id=content_id)
        style = cls.objects.get(id=style_id)

        transfer_basename = content.basename.split(".")[0] + "_" + \
                            style.basename.split(".")[0] + ".png"
        dummy_filepath = os.path.join(
            os.path.dirname(__file__), "static", "playground", "icons",
            "processing.png"
        )
        with open(dummy_filepath, "rb") as fp:
            transfer = cls.objects.create(
                image=ImageFile(fp, name=transfer_basename),
            )
        
        return transfer, messages.TRANSFER_SUCCESS.format(
            content.basename, style.basename,
        )


class Result(models.Model):
    transfer = models.ForeignKey(
        to=Image, 
        on_delete=models.CASCADE, 
        related_name='transfer'
    )
    content = models.ForeignKey(
        to=Image, 
        on_delete=models.CASCADE, 
        related_name='content'
    )
    style = models.ForeignKey(
        to=Image, 
        on_delete=models.CASCADE, 
        related_name='style'
    )

    sqs_client = boto3.client("sqs", endpoint_url=settings.AWS_SQS_ENDPOINT_URL)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.transfer_queue_message = {
            "request_type" : "transfer",
            "request_body" : {
                "transfer" : self.transfer.basename,
                "content" : self.content.basename,
                "style" : self.style.basename,
                "bucket" : settings.AWS_STORAGE_BUCKET_NAME,
                "s3_endpoint" : settings.AWS_S3_ENDPOINT_URL,
            }
        }


    def send_transfer_message(self):
        """
        send sqs queue a request message to transfer using images at s3
        """

        try:
            q_url = self.sqs_client.get_queue_url(QueueName=settings.AWS_SQS_QUEUE_NAME)

            res = self.sqs_client.send_message(
                QueueUrl=q_url["QueueUrl"], 
                MessageBody=json.dumps(self.transfer_queue_message),
            )
            return None
        except:
            return messages.TRANSFER_WARNING.format(
                settings.AWS_SQS_ENDPOINT_URL, settings.AWS_SQS_QUEUE_NAME,
            )