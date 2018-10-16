import logging
import textwrap
from nbconvert.preprocessors import Preprocessor


__all__ = ['RemoveInitializationCellPreprocessor',
           'RemoveBeforeSummaryPreprocessor',
           'RemoveCellJavaScript',
           'NewPagePreprocessor',
           'RemoveWarningsPreprocessor',
           'WrapPrintPreprocessor']


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


class NewPagePreprocessor(Preprocessor):
    """Adds a new page every time a header is encountered"""
    def preprocess(self, nb, resources):
        self.log.info("I'll keep only cells from ")

        processed_cells = []
        previous_cell_is_header = False
        for k, cell in enumerate(nb.cells):
            if k == 0:
                processed_cells.append(cell)
                continue
            elif cell['cell_type'] == 'markdown':
                if cell['source'].startswith('# '):  # Header
                    processed_cells.append({'cell_type': 'raw', 'metadata': {}, 'source': '\\newpage'})
                    previous_cell_is_header = True
                else:
                    if (cell['source'].startswith('## ')
                            and not previous_cell_is_header):  # Subheader
                        processed_cells.append({'cell_type': 'raw', 'metadata': {}, 'source': '\\newpage'})
                    previous_cell_is_header = False
            processed_cells.append(cell)

        nb.cells = processed_cells
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
