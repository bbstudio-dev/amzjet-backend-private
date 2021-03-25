import os

from airflow.models import DAG
from bb_utils.collections.helpers import merge_dicts
from bb_ext.airflow.utils import work_dir_name

##########################################################################
# Classes.
##########################################################################


class TaskRef(object):
    """ Fully-qualified task reference. """

    def __init__(self, task_id, dag_id=None):
        self.task_id = task_id
        self.dag_id = dag_id

    def __str__(self):
        if self.dag_id:
            return '%s.%s' % (self.dag_id, self.task_id)
        else:
            return self.task_id


class CustomMacros:
    """
    Commonly used macros.
    Typically require access to the current task instance (ti).
    """

    def __init__(self, dag):
        self.dag = dag

    def as_dict(self):
        return {'WORK_DIR_LOCAL': self.work_dir_local, 'WORK_DIR_GCS': self.work_dir_gcs}

    def work_dir_local(self, ti):
        dir_name = work_dir_name(self.dag.root_dag_id, ti.execution_date)
        dir_name = os.path.join(self.dag.settings.LOCAL_STAGE_DIR(), dir_name)
        path = os.path.abspath(dir_name)
        return path.rstrip('/')

    def work_dir_gcs(self, ti):
        dir_name = work_dir_name(self.dag.root_dag_id, ti.execution_date)
        path = os.path.join('gs://', self.dag.settings.GCS_STAGE_BUCKET(), self.dag.settings.GCS_STAGE_DIR(), dir_name)
        return path.rstrip('/')


class CustomDag(DAG):
    """ Airflow dag with added properties. """

    def __init__(self, dag_id, settings, **kwargs):
        super(CustomDag, self).__init__(dag_id, **kwargs)

        # Application settings.
        self.settings = settings


##########################################################################
# Helper functions.
##########################################################################


def create_dag(dag_fileloc, dag_id, settings, root_dag_id=None, **kwargs):
    dag = CustomDag(dag_id, settings, **kwargs)

    # Workaround for an issue reported here:
    # http://mail-archives.apache.org/mod_mbox/airflow-dev/201707.mbox/%3CCABVU3FENOXyvLJP1HRrpaWK8R1qXJrOO+YX121rBU+NBTspt7g@mail.gmail.com%3E
    dag.fileloc = dag_fileloc

    # Root dag id to access resources shared across subdags. Example:
    # path to the directory for staging files.
    dag.root_dag_id = root_dag_id or dag_id

    dag.user_defined_macros = merge_dicts([dag.user_defined_macros or {}, CustomMacros(dag).as_dict()])

    return dag


def create_subdag(dag_fileloc, parent_dag, subdag_id, **kwargs):
    """
    ATTENTION:

    There were reports that SubDagOperator may cause deadlocks:
    https://medium.com/bluecore-engineering/airflow-why-is-nothing-working-f705eb6b7b04

    There is workaround:
    https://medium.com/@team_24989/fixing-subdagoperator-deadlock-in-airflow-6c64312ebb10

    Bug:
    https://issues.apache.org/jira/browse/AIRFLOW-74 (FIXED in 1.10.0)

    DO NOT use sub-dags to avoid hitting other problems.
    """

    if 'default_args' not in kwargs:
        kwargs['default_args'] = parent_dag.default_args

    root_dag_id = parent_dag.root_dag_id

    dag = create_dag(
        dag_fileloc,
        dag_id='%s.%s' % (parent_dag.dag_id, subdag_id),
        settings=parent_dag.settings,
        root_dag_id=root_dag_id,
        **kwargs)

    dag.user_defined_macros = merge_dicts([parent_dag.user_defined_macros or {}, dag.user_defined_macros or {}])

    return dag
