import sys
import logging
from src import (load_config,
                 NotebookFolder)


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        log.info('No config provided, using .\config.yml')
        config_path = '.\config.yml'
    else:
        config_path = sys.argv[-1]
        log.info(f'Using config {config_path}')
    config = load_config(config_path)

    log.info('Parsing notebooks into LogFolder and LogNotebook objects')
    log_notebook_structure = NotebookFolder(path=config['base_dir'],
                                            name=config['name'],
                                            sections=config['sections'])

    log.info('Creating index notebooks')
    log_notebook_structure.compile_index_notebook()

    log.info('Generating templates')
    log_notebook_structure.generate_template(config=config['template'])

    log.info('Converting log notebooks to HTML')
    log_notebook_structure.convert_to_HTML(target_dir=config['html_target_dir'])

    log.info('Generating HTML Tipuesearch content')
    log_notebook_structure.generate_tipuesearch_content(
        save_path=config['html_target_dir'] / 'tipuesearch_content.js')

    log.info('Converting log notebooks to PDF')
    # log_notebook_structure.convert_to_PDF(target_dir=config['pdf_target_dir'])
    # Hannes_notebook = log_notebook_structure.notebook_folders[1].notebooks[3]
    # Hannes_notebook.convert_to_PDF(target_dir=config['pdf_target_dir'])
