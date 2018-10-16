import yaml
import logging
import pprint
from pathlib import Path
import string


__all__ = ['DEFAULT_CONF',
           'load_config',
           'generate_template']

logger = logging.getLogger(__name__)


DEFAULT_CONF = {
    'target_dir': 'doc',
    'log_notebook_structure': {
        'log_folders': [],
        'log_notebooks': []
    }
}


def _convert_dirs_to_paths(d):
    """Recursively convert all dirs to Paths"""
    for key, val in d.items():
        if isinstance(val, dict):
            d[key] = _convert_dirs_to_paths(val)
        elif key.endswith('_dir') or key.endswith('_folder'):
            d[key] = Path(val)
    return d



def load_config(config_path):
    """Load config from yml file, adding default values

    anything ending with 'dir' is converted with a path
    """
    with open(config_path, 'r') as f:
        conf = yaml.load(f)
    assert conf is not None, "No config.yml file found"

    # Add any missing items from DEFAULT_CONF
    conf.update({k:v for k,v in DEFAULT_CONF.items() if k not in conf})
    logger.debug(f'config: \n{pprint.pformat(conf)}')

    # Convert all elements ending with '_dir' to Paths recursively
    conf = _convert_dirs_to_paths(conf)

    return conf


class TemplateFormatter(string.Template):
    delimiter = '$%'


def generate_template(template_path, **kwargs):
    template_unformatted_str = template_path.read_text()
    template_unformatted = TemplateFormatter(template_unformatted_str)

    template = template_unformatted.substitute(**kwargs)
    template.strip()

    return template
