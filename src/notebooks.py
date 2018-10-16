from copy import copy
from typing import Union, List
from pathlib import Path
import logging
from traitlets.config import Config
from nbconvert import HTMLExporter
import nbformat
from nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell

from .converter_preprocessors import (RemoveInitializationCellPreprocessor,
                                      RemoveBeforeSummaryPreprocessor,
                                      RemoveCellJavaScript)
from .tools import generate_template


logger = logging.getLogger(__name__)


class Notebook:
    base_dir = None
    HTML_preprocessors = []
    template_config = {}

    def __init__(self, path, name: str = None, index: int = None,
                 read: bool = True, parent: 'NotebookFolder' = None,
                 template_config: dict = None):
        assert self.base_dir is not None, "Notebook.base_dir must be set"

        self.name = name
        self.index = index
        self.parent = parent

        if template_config is not None:
            Notebook.template_config = template_config

        # Set absolute and relative path
        if path is None:
            self.absolute_path = None
            self.relative_path = None
            self.level = None
        else:
            if path.is_absolute():
                self.absolute_path = path
                self.relative_path = path.relative_to(NotebookFolder.base_dir)
            else:
                self.absolute_path = self.base_dir / path
                self.relative_path = path
            self.level: int = len(self.relative_path.parents) - 1

        self.template_path = None
        self.HTML_path = None

        # Read notebook into nbformat Notebook object
        if read:
            self.notebook = nbformat.read(str(self.absolute_path),
                                          as_version=nbformat.NO_CONVERT)

    def __str__(self):
        if self.index is not None:
            return f'{self.index} - {self.name}'
        else:
            return self.name

    @property
    def cells(self):
        return self.notebook.cells

    @cells.setter
    def cells(self, cells):
        self.notebook.cells = cells

    @property
    def parents(self):
        if self.parent is None:
            return []
        else:
            return self.parent.parents + [self.parent]

    def get_link(self, base_path: Path, offset: int = 0):
        """Get relative HTML path of notebook with respect to base_path

        Args:
            base_path: Base path that is referring to current notebook
            offset: Any offset in difference between path levels
                e.g. if a notebook folder is requesting a link to another
                notebook on behalf of one of its children, the level is 1.
                The reason is that the child needs to ascend one more level

        """
        target_path = self.relative_path.with_suffix('.html')

        if base_path == Path():  # We're already at base
            return target_path

        for level, origin_path in enumerate(base_path.parents):
            try:
                relative_path = Path('../' * (level + offset))
                # Will raise error if target path is not subpath
                relative_path /= target_path.relative_to(origin_path)
                break
            except ValueError:
                pass
        else:
            raise ValueError(f'Could not determine {target_path} wrt {base_path}')

        return relative_path

    def convert_to_HTML(self,
                        target_dir: Path,
                        HTML_exporter: HTMLExporter = None):
        """Convert single log notebook to HTML

        Args:
            target_dir: Target directory for output HTML files
            HTML_exporter: exporter for converting notebook to HTML

        Returns:
            None
        """
        logger.info(f'Starting HTML conversion of {self.relative_path}')

        if HTML_exporter is None:
            config = Config()
            config.HTMLExporter.preprocessors = self.HTML_preprocessors
            HTML_exporter = HTMLExporter(config=config)

        if self.template_path is not None:
            HTML_exporter.template_file = str(self.template_path)

        # TODO ensure cells is synced

        # Convert notebook to HTML code
        HTML_output, _ = HTML_exporter.from_notebook_node(self.notebook,
                                                          resources=self.template_config)

        # Write HTML code into file
        self.HTML_path = target_dir / self.relative_path.with_suffix('.html')

        logger.info(f'writing to {self.HTML_path}')
        # Create dirs if they do not yet exist
        self.HTML_path.parent.mkdir(parents=True, exist_ok=True)

        with self.HTML_path.open('w', encoding='utf-8') as f:
            f.write(HTML_output)

        logger.info(f'HTML notebook converted: {self.relative_path}')

    def generate_template(self,
                          config: dict):
        """Generate a template file for a log notebook

        Args:
            config: Template config

        Returns:

        """
        self.template_config = copy(config)

        # Generate navigation bar sections
        self.template_config['navbar_sections'] = {}
        for name, section in NotebookFolder.sections.items():
            if 'notebook_folder' in section:
                section_notebook = section['notebook_folder'].index_notebook
            else:
                section_notebook = section['notebook']
            # Add offset=1 to link since the notebooks are one level down
            link = section_notebook.get_link(self.relative_path)

            self.template_config['navbar_sections'][name] = link

        self.template_config['site_libs_path'] = self.template_config['base_path'] / '../site-libs'
        self.template_config['parents'] = {str(parent): parent.index_notebook.get_link(self.relative_path)
                                           for parent in self.parents}
        self.template_config['notebook_name'] = str(self)
        self.template_path = self.template_config['template_dir'] / 'notebook.html'


class LogNotebook(Notebook):
    HTML_preprocessors = [RemoveCellJavaScript,
                          RemoveInitializationCellPreprocessor,
                          RemoveBeforeSummaryPreprocessor
                          ]

    def __init__(self,
                 path: Path,
                 name: str = None,
                 index: int = None,
                 read: bool = True,
                 parent: 'NotebookFolder' = None):
        super().__init__(path=path, name=name, index=index, read=read,
                         parent=parent)
        self.summary_cells = self.extract_summary_cells()

    def extract_summary_cells(self):
        start_index, stop_index = 0, 0
        for k, cell in enumerate(self.notebook.cells):
            if cell['cell_type'] != 'markdown':
                continue
            elif cell.source.lower().startswith('# summary'):
                start_index = k + 1
            elif start_index > 0 and cell.source.startswith('# '):
                stop_index = k
                break
        else:
            if start_index > 0:
                stop_index = len(self.notebook.cells)

        return self.notebook.cells[start_index:stop_index]


class SummaryNotebook(Notebook):
    HTML_preprocessors = [RemoveCellJavaScript,
                          RemoveInitializationCellPreprocessor,
                          ]
    pass


class LogIndexNotebook(Notebook):
    def __init__(self,
                 path: Path,
                 log_folder: 'NotebookFolder',
                 name: str,
                 parent: 'NotebookFolder' = None,
                 **kwargs):
        super().__init__(path=path, name=name, read=False, parent=parent,
                         **kwargs)
        self.log_folder = log_folder

    def compile(self):
        """
        Compile index notebook

        Returns:
            compiled index notebook

        """
        # Start with a fresh notebook
        self.notebook = new_notebook()

        if self.log_folder.summary_notebook:
            self.parse_summary_notebook(self.log_folder.summary_notebook)

        # Loop through log folder elements (sorted combined folders & files)
        for log_element in self.log_folder:
            if isinstance(log_element, NotebookFolder):
                self.parse_log_folder(log_element)
            elif isinstance(log_element, Notebook):
                self.parse_notebook(log_element)

        return self.notebook

    def parse_summary_notebook(self, summary_notebook):
        self.notebook.cells += summary_notebook.cells
        return summary_notebook.cells

    def parse_log_folder(self, log_folder):
        link = log_folder.index_notebook.get_link(self.relative_path)
        content = f'## <a href="{link}">{log_folder}</a>\n'

        contents = [*log_folder.notebook_folders, *log_folder.notebooks]

        for element in log_folder:
            link = element.get_link(self.relative_path)
            content += f'<a href="{link}">{element}</a><br>\n'

        cell = new_markdown_cell(content)
        self.notebook.cells.append(cell)
        return [cell]

    def parse_notebook(self, notebook):
        link = notebook.get_link(self.relative_path)
        content = f'## <a href="{link}">{notebook}</a>\n'

        if getattr(notebook, 'summary_cells', []):
            content += notebook.summary_cells[0]['source']

        cell = new_markdown_cell(content)
        self.notebook.cells.append(cell)
        return [cell]


class NotebookFolder:
    base_dir: Path = None
    template_config = {}
    sections = {}

    def __init__(self, path: Union[str, Path],
                 name: str = None,
                 index: int = None,
                 base_dir: Path = None,
                 parent: 'NotebookFolder' = None,
                 sections: list = None,
                 notebook_class = Notebook,
                 template_config: dict = None):
        self.name = name
        self.index = index
        self.parent = parent
        self.notebook_class = notebook_class

        # Update template settings if provided
        if template_config is not None:
            NotebookFolder.template_config = template_config
            Notebook.template_config = template_config

        # Convert to Path if necessary
        if not isinstance(path, Path):
            path = Path(path)

        if NotebookFolder.base_dir is None and base_dir is None:
            logger.info(f'Setting base dir to provided path {path}')
            base_dir = path

        if base_dir is not None:
            assert base_dir.is_absolute(), "Must provide absolute folder_path"
            NotebookFolder.base_dir = base_dir
            Notebook.base_dir = base_dir

        # Set absolute and relative path
        if path.is_absolute():
            self.absolute_path: Path = path
            self.relative_path: Path = path.relative_to(NotebookFolder.base_dir)
        else:
            self.absolute_path: Path = self.base_dir / path
            self.relative_path: Path = path
        self.level: int = len(self.relative_path.parents)

        # Extract notebooks and notebooks folders
        self.notebook_folders: List[NotebookFolder] = []
        self.notebooks: List[Notebook] = []
        self.summary_notebook: SummaryNotebook = None
        self.extract_folder_content(sections=sections)

        # Index notebook can be compiled via self.compile_index_notebook
        self.index_notebook: LogIndexNotebook = None

    def __iter__(self):
        contents = [*self.notebook_folders, *self.notebooks]

        # Sort contents if they all have an index
        if all(item.index is not None for item in contents):
            contents = sorted(contents, key=lambda element: element.index)

        return iter(contents)

    def __str__(self):
        if self.index is not None:
            return f'{self.index} - {self.name}'
        else:
            return self.name

    @property
    def parents(self):
        if self.parent is None:
            return []
        else:
            return self.parent.parents + [self.parent]

    def extract_folder_content(self, sections=None):
        if sections is None:
            # Extract log notebook folders and files (recursively)
            self.notebook_folders = self.extract_folders()
            folder_indices = [log_folder.index for log_folder in self.notebook_folders]

            self.notebooks = self.extract_files(ignore_indices=folder_indices,
                                                ignore_names=['summary'])
            file_indices = [log_file.index for log_file in self.notebooks]

            # TODO raise warning if combined indices are not sequential
        else:
            NotebookFolder.sections = {}
            for name, section in sections.items():
                if isinstance(section, str):  # Path provided instead of dict
                    path = section
                    notebook_class = Notebook
                else:
                    path = section['path']
                    # Convert notebook class from string to class
                    notebook_class = eval(section.get('notebook_class', 'Notebook'))

                if not isinstance(path, Path):  # Convert to Path
                    path = self.base_dir / path

                # register section
                NotebookFolder.sections[name] = {'path': path,
                                                 'notebook_class': notebook_class}

                if path.is_dir():  # Section is a folder
                    notebook_folder = NotebookFolder(path=path,
                                                     name=name,
                                                     index=None,
                                                     parent=self,
                                                     notebook_class=notebook_class)
                    self.notebook_folders.append(notebook_folder)
                    NotebookFolder.sections[name]['notebook_folder'] = notebook_folder
                elif path.suffix == '.ipynb':  # Section is a notebook
                    notebook = notebook_class(path=path,
                                              name=name,
                                              index=None,
                                              parent=self)
                    self.notebooks.append(notebook)
                    NotebookFolder.sections[name]['notebook'] = notebook
                else:
                    raise TypeError(f'Section {name} must be dir or notebook')

        # Extract optional summary notebook
        self.summary_notebook = self.extract_summary_notebook()

    def extract_folders(self) -> List['NotebookFolder']:
        """Extract notebook folders within current notebook folder

        If a folder does not have the form '{index} - {name}', it is filtered
        Notebook folders are sorted by their index
        """
        # Retrieve log folders (starting with an index)
        log_folder_paths = self.absolute_path.glob('[0-9]* - *')

        log_folders = []
        for log_folder_path in log_folder_paths:
            if not log_folder_path.is_dir():
                continue

            # extract index and name '{idx} - {name}'
            index, name = log_folder_path.stem.split(' - ', maxsplit=1)
            index = int(index)

            if index == 0 and name == 'Summary':
                continue

            log_folder = NotebookFolder(log_folder_path,
                                        name=name,
                                        index=index,
                                        parent=self,
                                        notebook_class=self.notebook_class)
            log_folders.append(log_folder)

        # Sort log folders by their index
        log_folders.sort(key=lambda log_folder: log_folder.index)

        return log_folders

    def extract_files(self, ignore_indices: List[int] = None,
                      ignore_names: List[str] = None):
        # Retrieve log notebooks (starting with an index)
        log_notebook_paths = self.absolute_path.glob('[0-9]* - *.ipynb')

        log_notebooks = []
        for log_notebook_path in log_notebook_paths:
            # extract index and name '{idx} - {name}'
            index, name = log_notebook_path.stem.split(' - ', maxsplit=1)
            index = int(index)

            if index in ignore_indices or name in ignore_names:
                logger.info(f'Ignoring notebook {log_notebook_path.name}')
                continue

            log_notebook = self.notebook_class(log_notebook_path,
                                               name=name,
                                               index=index,
                                               parent=self)
            log_notebooks.append(log_notebook)

        # Sort log notebooks by their index
        log_notebooks.sort(key=lambda log_notebook: log_notebook.index)
        return log_notebooks

    def extract_summary_notebook(self):
        # Add a summary notebook if it exists
        for path in self.absolute_path.iterdir():
            if path.name.lower().endswith('summary.ipynb'):
                return SummaryNotebook(path, name='Summary', index=None,
                                       parent=self)
        else:
            # No summary notebook found
            return None

    def get_link(self, base_path: Path, offset: int = 0):
        """Get relative link to index notebook with respect to base path"""
        assert self.index_notebook, "Cannot link to {self}: no index notebook"
        return self.index_notebook.get_link(base_path, offset=offset)

    def generate_template(self,
                          config: dict,
                          recursive=True):
        self.template_config = copy(config)

        self.template_config['base_path'] = Path('/'.join(['..'] * self.level))

        for log_notebook in self.notebooks:
            # Determine relative path of site_libs
            self.template_config['base_path'] = Path('/'.join(['..'] * log_notebook.level))
            log_notebook.generate_template(self.template_config)

        # Generate index template
        if self.index_notebook is not None:
            self.template_config['base_path'] = Path('/'.join(['..'] * self.index_notebook.level))
            self.index_notebook.generate_template(self.template_config)

        if recursive:
            for log_subfolder in self.notebook_folders:
                log_subfolder.generate_template(self.template_config)

    def convert_to_HTML(self,
                        target_dir: Path,
                        recursive: bool = True):
        """Convert notebooks in a folder structure to HTML files

        Args:
            target_dir: Target directory for output HTML files
            recursive: Also include subdirectories

        Returns:
            None
        """
        for log_notebook in self.notebooks:
            log_notebook.convert_to_HTML(target_dir=target_dir)

        if self.index_notebook is not None:
            self.index_notebook.convert_to_HTML(target_dir=target_dir)

        # Convert log notebook folders
        if recursive:
            for log_folder in self.notebook_folders:
                log_folder.convert_to_HTML(target_dir=target_dir)

    def compile_index_notebook(self,
                               filename: str = 'Index',
                               save: bool = False,
                               recursive: bool = True):
        """
        Compile index notebook from its notebooks and optional summary

        Args:
            filename: Name of the notebook (default 'Index').
                 Not relevant if save = False
            save: Save index notebook (default False)

        Returns:
            Index notebook

        Note:
            Index notebook is also saved to self.index_notebook
        """
        path = self.absolute_path / Path(filename).with_suffix('.ipynb')
        self.index_notebook = LogIndexNotebook(path=path,
                                               log_folder=self,
                                               name=self.name,
                                               index=self.index,
                                               parent=self.parent)

        if recursive:
            for log_folder in self.notebook_folders:
                log_folder.compile_index_notebook(filename=filename, save=save)

        self.index_notebook.compile()

        # TODO add save
        return self.index_notebook