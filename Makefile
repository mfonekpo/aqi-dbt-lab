.PHONY: \
	up down test-bucket-connection

up:
	docker compose --env-file "./.env" -f "./containers/airflow/docker-compose.yaml" up --build --wait
	docker compose -f "./containers/minio/docker-compose.yaml" up --build --wait

down:
	docker compose --env-file "./.env" -f "./containers/airflow/docker-compose.yaml" down
	docker compose -f "./containers/minio/docker-compose.yaml" down

test-bucket-connection:
.PHONY: test-minio-connection
test-minio-connection:
	docker compose --env-file .env -f containers/airflow/docker-compose.yaml exec -T airflow-worker python -c 'import os; from airflow.providers.amazon.aws.hooks.s3 import S3Hook; client = S3Hook(aws_conn_id="aqi_s3").get_conn(); bucket = os.environ["MINIO_BUCKET"]; client.head_bucket(Bucket=bucket); print("Connection OK:", bucket); client.head_bucket(Bucket="aqi-xcom"); print("Connection OK: aqi-xcom")'