import os
import pathlib
import shutil
import sphinx.util
import sys
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Learning Observer'
copyright = '2020-2025, Bradley Erickson'
author = 'Bradley Erickson'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
sys.path.insert(0, os.path.abspath('../'))

extensions = [
    'autodoc2',
    'myst_parser',
]

autodoc2_packages = [
    '../learning_observer/learning_observer',
    '../modules/writing_observer/writing_observer'
]

autodoc2_output_dir = 'apidocs'
autodoc2_member_order = 'bysource'

source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
    '.txt': 'markdown'
}

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']

LOGGER = sphinx.util.logging.getLogger(__name__)


def _copy_module_readmes(app):
    """Populate ``module_readmes`` with module README files."""

    docs_root = pathlib.Path(__file__).parent.resolve()
    modules_root = docs_root.parent / 'modules'
    destination_root = docs_root / 'module_readmes'

    if not modules_root.exists():
        LOGGER.warning("modules directory %s was not found", modules_root)
        return

    if destination_root.exists():
        shutil.rmtree(destination_root)
    destination_root.mkdir(parents=True, exist_ok=True)

    readme_paths = sorted(modules_root.glob('*/README.md'))
    for readme_path in readme_paths:
        module_name = readme_path.parent.name
        destination_path = destination_root / f"{module_name}.md"
        shutil.copy2(readme_path, destination_path)


def setup(app):
    app.connect('builder-inited', _copy_module_readmes)
