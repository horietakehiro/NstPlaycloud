from django.conf import settings
from playground.storages import MediaStorage

# UPLOAD
UPLOAD_SUCCESS="Image : {} is successfully uploaded."
UPLOAD_FAIL_INVALID="Image : {} is invalid. Upload fails."
UPLOAD_FAIL_DUPLICATED="Image : {} already exists. Upload fails"
UPLOAD_FAIL_S3ERROR="s3 endpoint is not correct or bucket is not created"

# DELETE
DELETE_SUCCESS="Image : {} is successfully deleted."
DELETE_FAIL_NOTEXISTS="ImageId : {} is not exists."
DELETE_FAIL_INVALID_METHOD="Delete operation accepts only POST method."
DELETE_WARNING="Queue message for deletion cannot' be sent. Endpoint : {} is wrong or Queue : {} does not exists."

# TRANSFER
TRANSFER_SUCCESS="Transfer is successfully requestd with content : {} / style : {}"
TRANSFER_FAIL_INVALID="Reuqest parameter is invalid." 
TRANSFER_FAIL_INVALID_METHOD="Transfer operation accepts only POST method."
TRANSFER_WARNING="Queue message for transfer cannot' be sent. Endpoint : {} is wrong or Queue : {} does not exists."

# MASKING
MASKING_FAIL_DATA_NOTFOUND="Masking fails. Result record with id : {} does not exist."
MASKING_FAIL_CANNOT_REQUEST="Masking fails. Request : {} could not be sent."

### messages for sqs
# DELETE
DELETE_QUEUE_MESSAGE = {
    "request_type" : "delete",
    "request_body" : {
        "basenames" : None,
        "bucket" : settings.AWS_STORAGE_BUCKET_NAME,
        "s3_endpoint" : settings.AWS_S3_ENDPOINT_URL,
        "prefixes" : [
            MediaStorage.location + "/" + "original/raw/",
            MediaStorage.location + "/" + "original/masked/",
            MediaStorage.location + "/" + "original/masked_inv/",
            MediaStorage.location + "/" + "original/binned/",
            MediaStorage.location + "/" + "original/binned_inv/",
            MediaStorage.location + "/" + "thumbnail/raw/",
            MediaStorage.location + "/" + "thumbnail/masked/",
            MediaStorage.location + "/" + "thumbnail/masked_inv/",
            MediaStorage.location + "/" + "thumbnail/binned/",
            MediaStorage.location + "/" + "thumbnail/binned_inv/",
        ],
    }
}

# TRANSFER
TRANSFER_QUEUE_MESSAGE = {
    "request_type" : "transfer",
    "request_body" : {
        "transfer_list" : None,
        "content_list" : None,
        "style_list" : None,

        "key_prefix" : MediaStorage.location + "/original/raw/",
        "bucket" : settings.AWS_STORAGE_BUCKET_NAME,
        "s3_endpoint" : settings.AWS_S3_ENDPOINT_URL,
    }
}

# MASKING
    # retdict["s3_endpoint"] = s3_endpoint
    # retdict["bucket"] = bucket
    # retdict["content"] = content
    # retdict["transfer"] = transfer

MASKING_MESSAGE = {
    "s3_endpoint" : settings.AWS_S3_ENDPOINT_URL,
    "bucket" : settings.AWS_STORAGE_BUCKET_NAME,
    "content" : None,
    "transfer" : None,
}