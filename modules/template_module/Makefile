TEMPLATE_MODULE_PATH := $(shell pwd)
TEST_MODULE_REPLAY_FILE := $(TEMPLATE_MODULE_PATH)/test_module_replay.json

instantiate:
    cd /tmp && cookiecutter TEMPLATE_MODULE_PATH
    cd <template_directory> && pip install --editable .

diff:
    diff -r <template_directory> <reference_directory>

install:
    cd <template_directory> && pip install --editable .

overwrite:
    cd <template_directory> && pip install --editable . --upgrade

test:
    cd .. && $(PYTHON) learning_observer

.PHONY: instantiate diff install overwrite test
