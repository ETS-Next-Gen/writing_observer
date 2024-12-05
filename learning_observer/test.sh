#!/bin/bash
# learning_observer/test.sh
echo "================================================="
echo "Running tests for Learning Observer"
echo "================================================="

# Modify the commands below to fit your testing needs
echo "Running doctests"
# Including the `learning_observer/` path will ignore
# our `util` and `prototype` directories. We ignore
# the `main.py` file as it expects us to pass command
# line arguments which interferes with PyTest's
# `--doctest-modules` flag.
pytest --doctest-modules learning_observer/ --ignore=learning_observer/main.py
