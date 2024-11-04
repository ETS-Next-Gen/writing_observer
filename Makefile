PACKAGES ?= wo,awe

run:
	# If you haven't done so yet, run: make install
	# we need to make sure we are on the virtual env when we do this
	cd learning_observer && python learning_observer

venv:
	# This is unnecessary since LO installs requirements on install.
	# pip install --no-cache-dir -r requirements.txt

# install commands
install: venv
	# The following only works with specified packages
	# we need to install learning_observer in dev mode to
	# more easily pass in specific files we need, such as creds
	pip install --no-cache-dir -e learning_observer/

	# Installing Learning Oberser (LO) Dash React Components
	# TODO properly fetch the current version of lodrc.
	# We have a symbolic link between `lodrc-current` and the most
	# recent version. We would like to directly fetch `lodrc-current`,
	# however, the fetch only returns the name of the file it's
	# linked to. We do an additional fetch for the linked file.
	@LODRC_CURRENT=$$(curl -s https://raw.githubusercontent.com/ETS-Next-Gen/lo_assets/main/lo_dash_react_components/lo_dash_react_components-current.tar.gz); \
	pip install https://raw.githubusercontent.com/ETS-Next-Gen/lo_assets/main/lo_dash_react_components/$${LODRC_CURRENT}

install-dev: venv
	# TODO create a dev requirements file
	pip install --no-cache-dir -e learning_observer/[${PACKAGES}]
	. ${HOME}/.nvm/nvm.sh && nvm use && pip install -v -e modules/lo_dash_react_components/

install-packages: venv
	pip install -e learning_observer/[${PACKAGES}]

	# Just a little bit of dependency hell...

	# The AWE Components are built using a specific version of
	# `spacy`. This requires an out-of-date `typing-extensions`
	# package. There are few other dependecies that require a
	# newer version. As far as I can tell, upgrading this package
	# does not effect the functionality we receive from the AWE
	# components.
	# TODO remove this extra step after AWE Component's `spacy`
	# is no longer version locked.
	# This is no longer an issue, but we will leave until all
	# dependecies can be resolved in the appropriate locations.
	# pip install -U typing-extensions

	# On Python3.11 with tensorflow, we get some odd errors
	# regarding compatibility with `protobuf`. Some installation
	# files are missing from the protobuf binary on pip.
	# Using the `--no-binary` option includes all files.
	pip uninstall -y protobuf
	pip install --no-binary=protobuf protobuf==4.25

# testing commands
test:
	# this is where we run doctests
	pytest modules/wo_highlight_dashboard

# Linting commands
linting-setup:
	# Setting up linting related packages
	pip install pycodestyle pylint
	npm install

linting-python:
	# Linting Python modules
	pycodestyle --ignore=E501,W503 $$(git ls-files 'learning_observer/*.py' 'modules/*.py')
	pylint -d W0613,W0511,C0301,R0913,too-few-public-methods $$(git ls-files 'learning_observer/*.py' 'modules/*.py')

linting-node:
	# TODO each of these have lots of errors and block
	# the next item from running
	# Starting to lint Node modules
	# Linting Javascript
	npm run lint:js
	# Linting CSS
	npm run lint:css
	# Finding any unused CSS files
	npm run find-unused-css

linting: linting-setup linting-python linting-node
	# Finished linting

build-writing-ext:
	# Installing LO Event
	cd modules/lo_event && npm install & npm link lo_event
	# Building extension
	cd extension/writing-process && npm install && npm run build
