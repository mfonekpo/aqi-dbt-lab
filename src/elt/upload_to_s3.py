from utils.logging_conf import logger
import json
from botocore.exceptions import (
    ClientError,
    BotoCoreError,
    NoCredentialsError,
    ParamValidationError,
)

class AirQualityLoadError(Exception):
    """Raised when uploading an air-quality response fails."""

def create_s3_key(
        data_interval_start,
        prefix="raw/aqi_values",
)-> str:
    interval_start = data_interval_start.in_timezone("UTC")

    return (
        f"{prefix}/"
        f"year={interval_start.year}/"
        f"month={interval_start.month:02d}/"
        f"day={interval_start.day:02d}/"
        f"hour={interval_start.hour:02d}/"
        "aqi.json"
    )



def upload_airquality_to_s3(
        data: bytes, s3_client, 
        metadata:dict, key: str, bucket:str="aqi"
) -> None:
    body = json.dumps(data).encode("utf-8")

    try:
        result = s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=body,
            ContentType="application/json",
            Metadata=metadata
        )

    except ClientError as error:
        code = error.response["Error"]["Code"]
        message = error.response["Error"]["Message"]

        if code == "AccessDenied":
            logger.error(f"Access denied when uploading to S3: {message}")
        elif code == "NoSuchBucket":
            logger.error(f"Bucket does not exist when uploading to S3: {message}")
        else:
            logger.exception(f"S3 returned as error: {message}")

        raise AirQualityLoadError(message) from error
    except NoCredentialsError as e:
        logger.error(
            f"{code}: {message}"
        )
        raise AirQualityLoadError("S3 credentials are missing") from e

    except ParamValidationError as e:
        logger.error(
            f"{code}: {message}"
        )
        raise AirQualityLoadError("Invalid upload parameters") from e

    except BotoCoreError as e:
        # Includes connection failures, timeouts, and other SDK failures.
        logger.exception("S3 SDK failure")
        raise AirQualityLoadError("S3 upload failed") from e
    return {
        "ETag": result.get("ETag"),
        "VersionId": result.get("VersionId"),
        "Key": result.get("Key"),
        "Bucket": bucket,
    }