# Documentation

## Build process

Using [Sphinx](https://www.sphinx-doc.org/en/master/) we automatically build the documentation using markdown files and docstrings from the code.

On pushes or pull requests to the main branch, the documentation is auto-built and available on [Readthedocs](https://readthedocs.org/).

## Including documentation

Since documentation is built from the code, you need to follow specific steps to include new documentation elements.

### Markdown file

To include a new markdown file in the documentation, follow these steps:

1. Place your markdown file in the `docs/` directory. Any images should be placed in `docs/_images`.
2. Add a reference to your markdown file in `autodocs/other_docs.rst`. The reference will look like this:

```rst
.. include:: ../docs/your_markdown_file.md
   :parser: myst_parser.sphinx_
```

Replace `your_markdown_file.md` with the name of your markdown file.

### Module

To include a newly added module in the documentation, follow these steps:

1. Add a reference to the module in `autodocs/modules.rst`. The reference will look like this:

```rst
.. autosummary::
   :recursive:
   :toctree: generated/your_module_name

   your_module_name
```

Replace `your_module_name` with the name of your module.

By following these steps, you can ensure that your new markdown files and modules are properly integrated into the documentation, which will then be automatically built and made available on Readthedocs.
