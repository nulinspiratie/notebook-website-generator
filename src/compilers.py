import os
import logging
import nbformat
from nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell
from nbconvert import HTMLExporter, LatexExporter, PDFExporter
from traitlets.config import Config

from .converter_preprocessors import (NewPagePreprocessor,
                                      RemoveWarningsPreprocessor,
                                      WrapPrintPreprocessor)


__all__ = ['NotebookCompiler',
           'CompactNotebookCompiler']

logger = logging.getLogger(__name__)


class NotebookCompiler:
    config = None
    preprocessors = [NewPagePreprocessor,
                     RemoveWarningsPreprocessor,
                     WrapPrintPreprocessor]
    measurement_config = {'start': 1, 'end': None}

    def __init__(self, name='', config=None):
        self.name = name
        if config:
            self.config = config

        self.source_dir = os.path.join(self.config['base_dir'],
                                       self.config['measurement_overview_folder'])

        self.notebook = new_notebook()

    def __str__(self):
        return self.name

    def parse_header_notebook(self, notebook_filename):
        logger.info(f'Parsing header notebook: {notebook_filename}')
        notebook_filepath = os.path.join(self.source_dir, notebook_filename)
        notebook = nbformat.read(notebook_filepath, as_version=nbformat.NO_CONVERT)
        self.notebook.cells += notebook.cells
        return notebook.cells

    def parse_measurement_notebook(self, notebook_filename, update=True):
        logger.info(f'Parsing measurement notebook: {notebook_filename}')
        notebook_filepath = os.path.join(self.source_dir, notebook_filename)
        notebook = nbformat.read(notebook_filepath, as_version=nbformat.NO_CONVERT)
        cells = notebook.cells

        # Clear optional template at the end of the notebook
        for k, cell in enumerate(cells):
            if cell['source'] == '# Template':
                cells = cells[:k]
                break

        # Optionally scrap initial and final cells
        if self.measurement_config['start'] is not None:
            cells = cells[self.measurement_config['start']:]
        if self.measurement_config['end'] is not None:
            cells = cells[:self.measurement_config['stop']]

        if update:
            self.notebook.cells += cells
        return cells

    def generate_combined_notebook(self, filepath=None):
        if filepath is None:
            filepath = self.config['temp_dir'] / f'measurement_overview_{self}.ipynb'
        logger.info(f'Generating combined notebook to {filepath}')
        with filepath.open('w', encoding='utf-8') as f:
            nbformat.write(self.notebook, f)

    def generate_pdf(self, filepath=None, config=None):
        if filepath is None:
            filepath = os.path.join(self.config['pdf_target_dir'],
                                    f'Measurement_overview_{self.name}.pdf')
        logger.info(f'Compiling mode {self} to {filepath}')

        if config is None:
            config = Config()
        config.PDFExporter.preprocessors = self.preprocessors
        pdf_exporter = PDFExporter(config=config)
        pdf_exporter.exclude_input = True
        pdf_output, _ = pdf_exporter.from_notebook_node(self.notebook)

        with open(filepath, 'wb') as f:
            f.write(pdf_output)
        logger.info(f'Compiled mode {self} to {filepath}')


class CompactNotebookCompiler(NotebookCompiler):
    def parse_measurement_notebook(self, notebook_filename, update=True):
        cells = super().parse_measurement_notebook(notebook_filename,
                                                          update=False)
        # Remove any cells after optional `Remaining measurements` header
        for k, cell in enumerate(cells):
            if cell['source'] == '# Remaining measurements':
                cells = cells[:k]
                break

        if update:
            self.notebook.cells += cells

        return cells