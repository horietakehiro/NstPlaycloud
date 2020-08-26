from transfer.common import config

TRANSFER_QUEUE_MESSAGE = {
    "request_type" : "transfer",
    "request_body" : {
        "transfer_list" : None,
        "content_list" : None,
        "style_list" : None,

        "bucket" : config.AWS_S3_BUCKET_NAME,
        "s3_endpoint" : config.AWS_S3_ENDPOINT_URL,
    }
}