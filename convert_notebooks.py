import logging
from src import (load_config,
                 NotebookFolder)


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

if __name__ == '__main__':
    config = load_config('.\config.yml')

    log.info('Parsing notebooks into LogFolder and LogNotebook objects')
    log_notebook_structure = NotebookFolder(path=config['base_dir'],
                                            name=config['name'],
                                            sections=config['sections'])

    # log.info('Removing most notebooks')
    # log_folder = log_notebook_structure.notebook_folders[1]
    # log_notebook_structure.notebook_folders = [log_folder]
    # log_folder.notebooks = []
    # log_subfolder = log_folder.notebook_folders[0]
    # log_folder.notebook_folders = [log_subfolder]
    # log_subfolder.notebooks = log_subfolder.notebooks[:5]
    # NotebookFolder.sections = {k: v for k, v in NotebookFolder.sections.items() if k == 'Analysis'}

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
