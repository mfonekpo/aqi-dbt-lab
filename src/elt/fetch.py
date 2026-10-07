import logging
import os
from typing import Any
import requests
from dotenv import load_dotenv
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.validate import AirqualityFetchError
from utils.logging_conf import logger


load_dotenv()

WEATHERAPI = os.getenv("WEATHERAPI")
LAT = os.getenv("LAT")
LONG = os.getenv("LONG")

API_URL = "https://api.openweathermap.org/data/2.5/air_pollution"
# Rate limits need a separate policy that respects the provider's retry delay.
RETRYABLE_STATUS_CODES = frozenset({500, 502, 503, 504})


class RetryableFetchError(AirqualityFetchError):
    """An acquisition failure that may succeed on a later attempt."""


def validate_env() -> None:
    if not all([WEATHERAPI, LAT, LONG]):
        raise EnvironmentError(
            "Missing required environment variables. "
            "WEATHERAPI, LAT, LONG must all be set"
        )


@retry(
    retry=retry_if_exception_type(RetryableFetchError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def fetch_air_quality() -> dict[str, Any]:
    """Fetch a successful, parseable JSON response and return its body as bytes."""

    validate_env()

    payload = {
        "lat": LAT,
        "lon": LONG,
        "appid": WEATHERAPI,
    }

    try:
        response = requests.get(API_URL, params=payload, timeout=(30, 30))
        response.raise_for_status()
        response.json()  # Validate JSON without reserializing the response body.

    except requests.exceptions.JSONDecodeError:
        raise AirqualityFetchError(
            "API response could not be parsed as JSON"
        ) from None

    except requests.exceptions.Timeout:
        raise RetryableFetchError("API request timed out") from None

    except requests.exceptions.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else None
        error_type = (
            RetryableFetchError
            if status in RETRYABLE_STATUS_CODES
            else AirqualityFetchError
        )
        # Requests error text can contain the URL, including the API key.
        raise error_type(f"API returned HTTP status {status}") from None

    except requests.exceptions.SSLError:
        raise AirqualityFetchError("API TLS connection failed") from None

    except requests.exceptions.ConnectionError:
        raise RetryableFetchError("API connection failed") from None

    except requests.exceptions.RequestException as exc:
        raise AirqualityFetchError(
            f"API request failed: {type(exc).__name__}"
        ) from None

    logger.info("API request succeeded and response passed JSON parsing")
    return response.json()