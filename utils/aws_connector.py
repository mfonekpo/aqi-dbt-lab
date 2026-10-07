import os
from utils.logging_conf import logger
import boto3
from botocore.config import Config
from botocore.exceptions import (
    ClientError,
    NoCredentialsError,
)


def create_s3_client():
    """Creates an S3 client using environment variables for configuration."""
    endpoint_url = os.getenv("S3_ENDPOINT_URL", "http://minio:9000")
    region_name = os.getenv("AWS_REGION", "us-east-1")
    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID", "admin")
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY", "password123")
    try:
        return boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            config=Config(
                s3={"addressing_style": "path"},
                connect_timeout=5,
                read_timeout=30,
                retries={"mode": "standard", "total_max_attempts": 3},
            ),
        )
    except ClientError as error:
        logger.error(
            f"{error.response['Error']['Code']}: {error.response['Error']['Message']}"
        )
        raise ClientError
    except NoCredentialsError as error:
        logger.error(
            f"{error.response['Error']['Code']}: {error.response['Error']['Message']}"
        )
        raise NoCredentialsError