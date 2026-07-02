from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    "start_date": datetime(2025, 1, 1),
}

with DAG(
    dag_id="bigquery_test_dag",
    default_args=default_args,
    schedule=None,
    catchup=False,
    tags=["bigquery"],
) as dag:

    def test_bigquery_connection():
        from google.cloud import bigquery

        client = bigquery.Client()
        query = """
            SELECT COUNT(*) AS total_rows
            FROM `ecom-intelligence-pipeline-001.ecom_bronze.bronze_orders`
        """

        query_job = client.query(query, location="US")
        result = query_job.result()
        for row in result:
            print(f"total_rows={row.total_rows}")

    test_query = PythonOperator(
        task_id="test_bigquery_connection",
        python_callable=test_bigquery_connection,
    )