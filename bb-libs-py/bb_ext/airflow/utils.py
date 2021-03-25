import os
import re

from airflow.models import BaseOperator
from bb_utils.time import utils as tu


def _get_task_id(task):
    if isinstance(task, BaseOperator):
        return task.task_id
    elif isinstance(task, str):
        return task
    raise ValueError('Argument must be an instance of a BaseOperator or a string.')


def _wrap_as_list(v):
    if isinstance(v, list):
        return v
    return [v]


def xcom_pull_expr(tasks):
    task_ids = map(_get_task_id, _wrap_as_list(tasks))
    task_ids_args = ', '.join(['"%s"' % t for t in task_ids])

    return '{{ti.xcom_pull(%s)}}' % task_ids_args


def id_from_str(phrase):
    """Converts the passed string into a lowercased identifier."""
    s = re.sub('[^0-9a-zA-Z]+', '_', phrase)
    s = re.sub('_{2,}', '_', s)
    return s.lower()


def id_from_file(filename, prefix=None):
    basename = os.path.basename(filename)
    result = id_from_str(basename)

    if prefix:
        result = '_'.join([str(prefix), result])
    return result


def make_sub_id(flow_id, task_id):
    return '_'.join([flow_id.rstrip('_'), task_id.lstrip('_')])


def date_for_path(d):
    """Returns date formatted as 2019-02-04T20:50:06.731130 in UTC tz."""
    d = tu.utc_time(d)
    return d.strftime('%Y-%m-%dT%H:%M:%S.%f')


def work_dir_name(dag_id, exec_date, remove_version_suffix=True):
    if remove_version_suffix:
        dag_id = re.sub(r'_v\d+$', '', dag_id)

    exec_date_str = date_for_path(exec_date)
    work_dir_path = '%s/%s' % (dag_id, exec_date_str)
    return work_dir_path


def file_from_id(id):
    return id.replace('_', '-')


def dated_path(domain, dir_name, file_name, target_date, root_path=None):
    """
    Generates a simple dated path (not time component). This scheme should be ised in
    cases when there are no multiple timestamped versions of the data to be stored
    per day.
    """
    yyyy_mm_dd = '%04d-%02d-%02d' % (target_date.year, target_date.month,
                                     target_date.day)

    path = '{0}/{1}/{2}/{3}'.format(domain, dir_name, yyyy_mm_dd, file_name)

    if root_path:
        path = os.path.join(root_path, path)

    return path


def begin_strict_bash(cmd):
    return """
    set -euo pipefail
    """ + cmd
