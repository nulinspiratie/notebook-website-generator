import re
from typing import Union
from copy import copy
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
        elif key.endswith('_dir') or key.endswith('_folder') or key.endswith('_file'):
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

    if 'latex_macros_file' in conf:  # Add latex
        latex_macros_filepath = conf['base_dir'] / conf['latex_macros_file']
        conf['template']['latex_macros'] = latex_macros_filepath.read_text()

    return conf


class TemplateFormatter(string.Template):
    delimiter = '$%'


def generate_template(template_path, **kwargs):
    template_unformatted_str = template_path.read_text()
    template_unformatted = TemplateFormatter(template_unformatted_str)

    template = template_unformatted.substitute(**kwargs)
    template.strip()

    return template


cell_header_regex = re.compile('(#+) (.+)')
def get_line_information(line: str) -> dict:
    """Get information about a (potential) markdown header line

    Args:
        line: Markdown line that is potentially a header

    Returns:
        Dict containing information about the line. Keys are:

        - is_header: Whether the line is a header or not
        - level: Header level (only passed if line is a header)
        - title: Header title (only passed if line is a header)
    """
    if cell_header_regex.match(line):
        hashtags, title = cell_header_regex.match(line).groups()
        return {'is_header': True,
                'level': len(hashtags),
                'title': title}
    else:
        return {'is_header': False}


def get_minimum_header_level(cells: list):
    minimum_level = None
    for cell in cells:
        if cell['cell_type'] != 'markdown':
            continue

        for line in cell['source'].splitlines():
            line_information = get_line_information(line)
            if line_information['is_header'] and \
                    (minimum_level is None or line_information['level'] < minimum_level):
                minimum_level = line_information['level']
    return minimum_level


def increase_header_level(cells: list,
                          min_level: int = None,
                          scale_all: Union[int, bool] = False):
    """Increase header levels of all cells.

    The header levels can either be capped to a minimum level (via min_level),
    or they can all be scaled via scale_all.
    If min_level is set, and scale_all is set to True, all levels are scaled
    such that the minimum level is equal to min_level

    Args:
        cells: List of notebook cells usually from notebook.cells
        min_level: Minimum header level (default None). If set to an integer,
            and scale_all is False, only the headers with a lower level than
            min_level are set to level min_level. If scale_all is True, all
            headers are rescaled such that the minimum header level is equal to
            min_level.
        scale_all: If set to an integer and min_level is False, all headers are
            rescaled by the integer amount.

    Returns:
        Cells with modified headers
    """
    assert min_level is not None or scale_all is not False, \
        "Must either provide min_level or scale_all"

    if min_level is not None and scale_all:
        # All headers need to be reduced such that the lowest-level header is
        # equal to min_level. Here we find the current lowest-level header, from
        # which we know what the value of scale_all should be
        current_min_level = get_minimum_header_level(cells)
        if current_min_level is None:  # No headers
            return cells

        scale_all = min_level - current_min_level
        if scale_all <= 0:
            logger.info('No header level reducing necessary')
            return cells

        # Reset min_level to None
        min_level = None

    modified_cells = []
    for cell in cells:
        if cell['cell_type'] != 'markdown':
            modified_cells.append(cell)
            continue

        # Modify lines that are headers
        modified_cell_lines = []
        for line in cell['source'].splitlines():
            line_information = get_line_information(line)
            if line_information['is_header']:
                level = line_information['level']
                if min_level is not None and level < min_level:
                    level = min_level
                elif scale_all is not False:
                    level += scale_all
                line = f'{"#" * level} {line_information["title"]}'
            modified_cell_lines.append(line)

        # Copy cell, update source and add to modified cells
        modified_cell = copy(cell)
        modified_cell['source'] = '\n'.join(modified_cell_lines)
        modified_cells.append(modified_cell)

    return modified_cells


internal_link_regex = re.compile('\[(?P<text>.+)\]\(#(?P<link>.+)\)')
external_link_regex = re.compile('\[(?P<text>.+)\]\((?P<link>.+)\.ipynb\)')
def reroute_internal_links(cells: list, base_link: str):
    """Reroute all base links in cells"""
    modified_cells = []
    for cell in cells:
        modified_cell = copy(cell)
        if cell['cell_type'] == 'markdown':
            # Include base link in internal links
            modified_cell['source'] = internal_link_regex.sub(
                f'[\g<text>]({base_link}#\g<link>)',
                cell['source'])

            # Modify external notebook links to have suffix .html
            modified_cell['source'] = external_link_regex.sub(
                f'[\g<text>](\g<link>.html)',
                modified_cell['source'])

        modified_cells.append(modified_cell)

    return modified_cells