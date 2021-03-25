import datetime

from airflow.operators.dummy_operator import DummyOperator

import bb_ext.airflow.utils as af_utils


def test_xcom_pull_expr_for_single_id():
    assert af_utils.xcom_pull_expr('my_task_id') == '{{ti.xcom_pull("my_task_id")}}'

    op = DummyOperator(dag=None, task_id='my_task_id')
    assert af_utils.xcom_pull_expr(op) == '{{ti.xcom_pull("my_task_id")}}'


def test_id_from_str():
    assert af_utils.id_from_str("abc") == "abc"
    assert af_utils.id_from_str("abc_123") == "abc_123"
    assert af_utils.id_from_str("abc-123") == "abc_123"
    assert af_utils.id_from_str("a$!$%123") == "a_123"


def test_id_from_file():
    assert af_utils.id_from_file("gs://bucket/*/keywords_*.csv", "gcs") == "gcs_keywords_csv"  # noqa


def test_dated_path():
    ts = datetime.datetime(2019, 1, 16, 12, 17, 18, 30)
    path = af_utils.dated_path(
        domain='amazon.com',
        dir_name='bestsellers',
        file_name='bestsellers-books.json',
        target_date=ts,
        root_path='gs://my-bucket')
    assert path == "gs://my-bucket/amazon.com/bestsellers/2019-01-16/bestsellers-books.json"


def test_work_dir_name():
    d = datetime.datetime(2019, 2, 4, 20, 50, 6, 731130)
    assert af_utils.work_dir_name('my_dag_v10', d) == 'my_dag/2019-02-04T20:50:06.731130'
