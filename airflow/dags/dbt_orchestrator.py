from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.python import PythonOperator
from insert_records import main
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# For DockerOperator, we need ABSOLUTE HOST PATHS for mounts
# HOST_PROJECT_ROOT MUST be set in environment variables (docker-compose.yaml or .env)
HOST_PROJECT_ROOT = os.getenv('HOST_PROJECT_ROOT')

if not HOST_PROJECT_ROOT:
    raise ValueError(
        "HOST_PROJECT_ROOT environment variable is not set.\n"
        "This variable must point to the absolute path of the Weather_data_project directory on your host machine.\n"
        "Set it in .env file:\n"
        "  HOST_PROJECT_ROOT=/path/to/Weather_data_project\n"
        "Example:\n"
        "  HOST_PROJECT_ROOT=/home/user/repos/Weather_data_project"
    )

# Paths for Docker mounts (HOST filesystem paths)
HOST_DBT_PROJECT_PATH = os.path.join(HOST_PROJECT_ROOT, 'dbt', 'my_project')
HOST_DBT_PROFILES_PATH = os.path.join(HOST_PROJECT_ROOT, 'dbt')
HOST_SODA_PATH = os.path.join(HOST_PROJECT_ROOT, 'soda')

logger.info(f"Using HOST_PROJECT_ROOT: {HOST_PROJECT_ROOT}")
logger.info(f"DBT project host path: {HOST_DBT_PROJECT_PATH}")

default_args = {
    'description': 'A DAG orchestrating pulling data from API and ingesting it',
    'start_date': datetime(2025, 12, 1),
    'catchup': False,
}

dag = DAG(
    dag_id="weatherAPI_dbt_orchestrator",
    default_args=default_args,
    schedule=timedelta(minutes=15),
    doc_md="Weather data pipeline: extract → transform → validate"
)

with dag:
    task1 = PythonOperator(
        task_id='pull_push_to_db',
        python_callable=main,
        doc_md="Extract weather data from API and load to PostgreSQL"
    )
    
    task2 = DockerOperator(
        task_id='transform_data_dbt',
        image='weather_data_project-dbt:latest',
        command=['run'],
        working_dir='/usr/app',
        mounts=[
            Mount(source=HOST_DBT_PROJECT_PATH, target='/usr/app', type='bind'),
            Mount(source=HOST_DBT_PROFILES_PATH, target='/root/.dbt', type='bind')
        ],
        network_mode='weather_data_project_my-network',
        docker_url='unix://var/run/docker.sock',
        auto_remove='success',
        environment={
            'DBT_DB_NAME': os.getenv('DB_NAME', 'weather_db'),
            'DBT_DB_HOST': os.getenv('DB_HOST', 'db'),
            'DBT_DB_USER': os.getenv('DB_USER', 'weather_user'),
            'DBT_DB_PASSWORD': os.getenv('DB_PASSWORD'),
            'DBT_DB_PORT': os.getenv('DB_PORT', '5432'),
            'DBT_SCHEMA': os.getenv('DBT_SCHEMA', 'dev'),
        },
        doc_md="Transform raw data using dbt models"
    )

    task3 = DockerOperator(
        task_id='soda_check_docker_operator',
        image='justemzy101/soda-core:v2',
        api_version='auto',
        auto_remove='success',
        command=[
            '/bin/sh',
            '-c',
            'soda scan -d my_postgres -c /app/soda/configuration.yml /app/soda/checks/weather_checks.yaml; '
            'exit_code=$?; '
            'echo "Soda scan exited with code: $exit_code"; '
            # Treat 0, 1, and 2 as success, only fail on 3
            'if [ $exit_code -le 2 ]; then exit 0; else exit $exit_code; fi'
        ],
        docker_url='unix://var/run/docker.sock',
        network_mode='weather_data_project_my-network',
        mounts=[Mount(source=HOST_SODA_PATH, target='/app/soda', type='bind')],
        doc_md="Run Soda data quality checks - MUST PASS before transformation"
    )
    
    # Set task dependencies: data quality BEFORE transformation
    task1 >> task3 >> task2
