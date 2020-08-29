SQS_CANNOT_CONNECT="SQS endpoint : {} cannot be connected, or queue : {} does not exist."
SQS_NO_MESSAGE_STORED="SQS queue : {} stores no message."
S3_CANNOT_CONNECT_DOWNLOAD="S3 endpoint : {} cannot be connected, or bucket : {} does not exist, or images : {}, {} do not exist."
S3_CANNOT_CONNECT_UPLOAD="S3 endpoint : {} cannot be connected, or bucket : {} does not exist. Image : {} ualoading failed."

# messages for response
TRANSFER_SUCCESS="Transfer : {} has succeeded with size : {}."
TRANSFER_FAIL_SQS_ERROR="Transfer has failed. SQS endpoint : {} is wrong, or queue : {} does not exists."
TRANSFER_FAIL_NO_MESSAGE="Transfer has failed. SQS queue : {} at endpoint: {} has no message."
TRANSFER_FAIL_S3_DOWNLOAD_ERROR="Transfer : {} has failed. S3 endpoint : {} is wrong, or bucket : {} does not exist, or images : {} are does not exist."
TRANSFER_FAIL_S3_UPLOAD_ERROR="Transfer : {} succeede but result uploading failed. S3 endpoint : {} is wrong, or bucket : {} does not exist."

RESPONSE_BODY = {
    "message_list" : []
}