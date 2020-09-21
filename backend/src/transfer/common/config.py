import os

### AWS
AWS_REGION=os.environ.get("AWS_REGION", "ap-northeast-1")
AWS_S3_ENDPOINT_URL=os.environ.get("AWS_S3_ENDPOINT_URL", None)
AWS_S3_BUCKET_NAME=os.environ.get("AWS_S3_BUCKET_NAME", "nstpc")
AWS_SQS_ENDPOINT_URL=os.environ.get("AWS_SQS_ENDPOINT_URL", None)
AWS_SQS_TRANSFER_QUEUE_NAME=os.environ.get("AWS_SQS_TRANSFER_QUEUE_NAME", "nstpc-transfer")

### preprocess
IMAGE_DIR=os.path.join(os.path.dirname(__file__), "..", "..", "images")
MAX_IMAGE_SIZE=int(os.environ.get("MAX_IMAGE_SIZE", 512))

### engine
EPOCH=int(os.environ.get("EPOCH", 500))
CONTENT_LAYERS=['block5_conv2']
STYLE_LAYERS=['block1_conv1', 'block2_conv1', 'block3_conv1', 'block4_conv1', 'block5_conv1']

# for Adam optimizer
LEARNIGN_RATE=0.02
BETA_1=0.99
EPSILON=0.1

# weights for loss
CONTENT_WEIGHTS=10000
STYLE_WEIGHTS=0.01
TOTAL_VARIATION_WEIGHTS=30
