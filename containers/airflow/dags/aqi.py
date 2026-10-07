"""Capture OpenWeather air-quality responses every minute for comparison."""

from datetime import timedelta
from airflow.sdk import dag, task, get_current_context
import pendulum


@task(retries=2)
def fetch_data():
    from src.elt.fetch import fetch_air_quality

    
    return fetch_air_quality()


@task(retries=2)
def load_to_s3(data):
    from src.elt.upload_to_s3 import upload_airquality_to_s3, create_s3_key
    from utils.aws_connector import create_s3_client

    context = get_current_context()
    interval_start = context["data_interval_start"]


    s3_client = create_s3_client()
    metadata = {
    "source": "openweathermap-air-pollution",
    "dag-run-id": context["dag_run"].run_id,
    "data-interval-start": interval_start.isoformat(),
    "ingested-at": pendulum.now("UTC").isoformat(),
    "schema-version": "1",
    }
    key = create_s3_key(interval_start)
    return upload_airquality_to_s3(data, s3_client, metadata, key)


@dag(
    # dag_id="air_quality_every_minute",
    description="Fetch air-quality JSON every minute and upload it to aqi-staging.",
    schedule="@hourly",
    start_date=pendulum.datetime(2026, 9, 1, tz="UTC"),
    catchup=False,
    max_active_runs=3,
    is_paused_upon_creation=False,
    default_args={
        "retries": 2,
        "retry_delay": timedelta(minutes=1),
    },
    tags=["air-quality", "experiment"]
)
def extractor():
    data = fetch_data()
    load_to_s3(data)
extractor()
