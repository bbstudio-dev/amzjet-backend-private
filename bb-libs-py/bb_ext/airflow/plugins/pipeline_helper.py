import logging
import os
from subprocess import check_call
import tempfile

from airflow.models import BaseOperator
from airflow.plugins_manager import AirflowPlugin
from airflow.utils.decorators import apply_defaults


##############################################################################
# Helpers
##############################################################################

def add_symlinks_to_dir(files_to_link, target_dir=None, options={}):
    logger = options.get('logger') or logging.getLogger()

    if target_dir is None:
        target_dir = tempfile.mkdtemp()
        logger.info('Created temporary dir <%s>' % target_dir)
    else:
        logger.info('Preparing target directory <%s>...' %
                    target_dir)
        check_call('rm -rf %s' % target_dir, shell=True)
        check_call('mkdir -p %s' % target_dir, shell=True)

    for file_pattern in files_to_link:
        logger.info('Linking <%s> ...' % file_pattern)
        check_call('ln -s %s %s' % (file_pattern, target_dir), shell=True)

    return target_dir


##############################################################################
# Operators
##############################################################################

class BuildPySourceDist(BaseOperator):
    """
    Builds a source distributive (sdist) by creating symbolic links to the
    required files and then executing a setup.py.
    """

    template_fields = ('files_to_link', 'target_dir')
    ui_color = '#fad390'

    @apply_defaults
    def __init__(self, files_to_link, target_dir=None, python_path=None,
                 *args, **kwargs):
        super(BuildPySourceDist, self).__init__(*args, **kwargs)
        self.python_path = python_path
        self.files_to_link = files_to_link
        self.target_dir = target_dir

    def execute(self, context):
        add_symlinks_to_dir(self.files_to_link, self.target_dir)

        python_path = self.python_path or 'python'
        check_call(
            'cd {dir} && {py} {dir}/setup.py sdist'.format(
                dir=self.target_dir, py=python_path),
            shell=True)

        return os.path.join(self.target_dir, 'dist')


##############################################################################
# Plugin definition
##############################################################################

class PipelineSetupPlugin(AirflowPlugin):
    name = "pipeline_setup_plugin"
    operators = [BuildPySourceDist]
