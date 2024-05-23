PACKAGES ?= wo,awe

run:
	# If you haven't done so yet, run: make install
	# we need to make sure we are on the virtual env when we do this
	cd learning_observer && python learning_observer

venv:
	pip install --no-cache-dir -r requirements.txt

# install commands
install: venv
	# The following only works with specified packages
	# we need to install learning_observer in dev mode to
	# more easily pass in specific files we need, such as creds
	pip install --no-cache-dir -e learning_observer/[${PACKAGES}]
	# TODO resolve the lodrc-current symlink and fetch that url instead
	@LODRC_CURRENT=$$(curl -s https://raw.githubusercontent.com/ETS-Next-Gen/lo_assets/main/lo_dash_react_components/lo_dash_react_components-current.tar.gz); \
	pip install https://raw.githubusercontent.com/ETS-Next-Gen/lo_assets/main/lo_dash_react_components/$${LODRC_CURRENT}

install-dev: venv
	# TODO create a dev requirements file
	pip install --no-cache-dir -e learning_observer/[${PACKAGES}]
	. ${HOME}/.nvm/nvm.sh && nvm use && pip install -v -e modules/lo_dash_react_components/

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
