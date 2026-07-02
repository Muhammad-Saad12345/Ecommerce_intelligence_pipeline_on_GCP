from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from pendulum import datetime
from airflow.timetables.trigger import CronTriggerTimetable

with DAG(
    dag_id="ecommerce_dbt_pipeline",
    start_date=datetime(year=2026, month=6, day=20),
    schedule="*/5 * * * *",
    is_paused_upon_creation=False,
    catchup=False,
) as dag:

    build_silver = BashOperator(
        task_id="build_silver",
        bash_command="""
        cd /opt/airflow/dbt &&
        dbt build --select silver
        """
    )

    build_gold = BashOperator(
        task_id="build_gold",
        bash_command="""
        cd /opt/airflow/dbt &&
        dbt build --select gold
        """
    )

    # dbt build runs run + test in a single command, so we only need two tasks
    build_silver >> build_gold