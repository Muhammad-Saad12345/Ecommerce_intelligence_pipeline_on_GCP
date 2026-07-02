from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator


with DAG(
    dag_id="ecommerce_transformation_dag",
    start_date=datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
    tags=["ecommerce"]
) as dag:

    run_silver = BashOperator(
        task_id="run_silver",
        bash_command="""
        docker run --rm ecom-pipeline dbt run --select silver
        """
    )

    test_silver = BashOperator(
        task_id="test_silver",
        bash_command="""
        docker run --rm ecom-pipeline dbt test --select silver
        """
    )

    run_gold = BashOperator(
        task_id="run_gold",
        bash_command="""
        docker run --rm ecom-pipeline dbt run --select gold
        """
    )

    test_gold = BashOperator(
        task_id="test_gold",
        bash_command="""
        docker run --rm ecom-pipeline dbt test --select gold
        """
    )

    run_silver >> test_silver >> run_gold >> test_gold