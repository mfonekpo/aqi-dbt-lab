FROM apache/airflow:3.3.1

# Install only the dependencies required by the minute-capture experiment.
COPY requirements.txt /requirements.txt

RUN pip install --no-cache-dir -r /requirements.txt
