from transfer.common import config, messages

class SQSConnectionError(Exception):

    def __init__(self, endpoint, queue, *args, **kwargs):
        super(SQSConnectionError, self).__init__(*args, **kwargs)
        self.endpoint = endpoint
        self.queue = queue

    def get_message(self):

        return messages.TRANSFER_FAIL_SQS_ERROR.format(
            self.endpoint, self.queue
        )

class SQSNoMessageError(Exception):

    def __init__(self, endpoint, queue, *args, **kwargs):
        super(SQSNoMessageError, self).__init__(*args, **kwargs)
        self.endpoint = endpoint
        self.queue = queue

    def get_message(self):
        return messages.TRANSFER_FAIL_NO_MESSAGE.format(
            self.endpoint, self.queue
        )


class S3DownloadError(Exception):
    def __init__(self, transfer, endpoint, bucket, content, style, *args, **kwargs):
        super(S3DownloadError, self).__init__(*args, **kwargs)
        self.transfer = transfer
        self.endpoint = endpoint
        self.bucket = bucket
        self.content = content
        self.style = style


    def get_message(self):
        return messages.TRANSFER_FAIL_S3_DOWNLOAD_ERROR.format(
            self.transfer, self.endpoint, self.bucket, [self.content, self.style],
        )


class S3UploadError(Exception):
    def __init__(self, transfer, endpoint, bucket, *args, **kwargs):
        super(S3UploadError, self).__init__(*args, **kwargs)
        self.transfer = transfer
        self.endpoint = endpoint
        self.bucket = bucket

    def get_message(self):
        return messages.TRANSFER_FAIL_S3_UPLOAD_ERROR.format(
            self.transfer, self.endpoint, self.bucket,
        )
