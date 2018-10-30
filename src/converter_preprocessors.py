import logging
import textwrap
from nbconvert.preprocessors import Preprocessor
from nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell, new_raw_cell
from nbformat import from_dict


__all__ = ['RemoveInitializationCellPreprocessor',
           'RemoveBeforeSummaryPreprocessor',
           'RemoveCellJavaScript',
           'NewPagePreprocessor',
           'RemoveWarningsPreprocessor',
           'WrapPrintPreprocessor',
           'AddTitlePreprocessor',
           'InteractivePlotToStaticPreProcessor']


logger = logging.getLogger(__name__)


class RemoveInitializationCellPreprocessor(Preprocessor):
    def preprocess(self, nb, resources):
        for k, cell in enumerate(nb.cells):
            if 'silq.initialize' in cell['source']:
                nb.cells = nb.cells[k+1:]
                break
        return nb, resources


class RemoveBeforeSummaryPreprocessor(Preprocessor):
    def preprocess(self, nb, resources):
        for k, cell in enumerate(nb.cells):
            if cell['cell_type'] is not 'markdown':
                continue
            elif cell.get('source').lower().startswith('# summary'):
                nb.cells = nb.cells[k:]
                break
        return nb, resources


class RemoveCellJavaScript(Preprocessor):
    def preprocess(self, nb, resources):
        for k, cell in enumerate(nb.cells):
            if cell['cell_type'] != 'code':
                continue
            outputs = []
            for output in cell['outputs']:
                if 'application/javascript' in output.get('data', {}):
                    continue
                outputs.append(output)
            cell['outputs'] = outputs
        return nb, resources


class RemoveWarningsPreprocessor(Preprocessor):
    """Remove any warning outputs in code cells"""
    def preprocess(self, nb, resources):
        for k, cell in enumerate(nb.cells):
            if cell['cell_type'] == 'code':
                cell['outputs'] = [output for output in cell['outputs']
                                   if output.get('name') !='stderr']
        return nb, resources


class WrapPrintPreprocessor(Preprocessor):
    """Wrap too lengthy print statements"""
    def preprocess(self, nb, resources):
        for k, cell in enumerate(nb.cells):
            if cell['cell_type'] == 'code':
                for output in cell['outputs']:
                    if 'text' in output:
                        lines = output['text'].splitlines()
                        wrapped_lines = [textwrap.fill(line, width=90,
                                                       subsequent_indent='    ')
                                         for line in lines]
                        output['text'] = '\n'.join(wrapped_lines)
        return nb, resources


class AddTitlePreprocessor(Preprocessor):
    def preprocess(self, nb, resources):
        title_cell = new_raw_cell(f'<h1>{resources["notebook_name"]}</h1>')
        nb.cells.insert(0, title_cell)
        return nb, resources


### PDF preprocessors

class NewPagePreprocessor(Preprocessor):
    """Adds a new page every time a header is encountered"""
    def preprocess(self, nb, resources):
        logger.info('Adding page breaks before headers')

        processed_cells = []
        previous_cell_is_header = False
        for k, cell in enumerate(nb.cells):
            if k == 0:
                processed_cells.append(cell)
                continue
            elif cell['cell_type'] == 'markdown':
                if cell['source'].startswith('# '):  # Header
                    new_page_cell = from_dict({'cell_type':
                                                   'raw', 'metadata': {},
                                               'source': '\\newpage'})
                    processed_cells.append(new_page_cell)
                    previous_cell_is_header = True
                else:
                    if (cell['source'].startswith('## ')
                            and not previous_cell_is_header):  # Subheader
                        new_page_cell = from_dict({'cell_type': 'raw',
                                                   'metadata': {},
                                                   'source': '\\newpage'})
                        processed_cells.append(new_page_cell)
                    previous_cell_is_header = False
            processed_cells.append(cell)

        nb.cells = processed_cells
        return nb, resources


class InteractivePlotToStaticPreProcessor(Preprocessor):
    """Preprocessor that converts all interactive plots to static ones.

    Interactive plots are saved when ``%matplotlib interactive`` is used in the
    notebook. This results in the image not displaying when converted to PDF
    """
    def preprocess(self, nb, resources):
        for cell in nb.cells:
            if cell['cell_type'] != 'code':
                continue

            for output in cell['outputs']:
                html_output = output['data'].get('text/html', '')
                if html_output.startswith('<img src="data:image/png;base64,'):
                    image_source = html_output.split('"')[1] # Only keep within first "
                    image_source = image_source.split(',')[1] # Remove begining data:...
                    output['data']['image/png'] = image_source

        return nb, resources

