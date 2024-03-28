PACKAGES ?= wo,awe
VENV ?= .makevenv
PYTHON = ${VENV}/bin/python
PIP = ${VENV}/bin/pip

run:
	# we need to make sure we are on the virtual env when we do this
	cd learning_observer && ../${PYTHON} learning_observer

clean: clean-venv
	# Finished all the cleaning

venv:
	virtualenv ${VENV}
	${PIP} install --no-cache-dir -r requirements.txt
clean-venv:
	# Removing the virtual environment
	rm -rf ${VENV}

# install commands
install: venv
	# The following only works with specified packages
	# we need to install learning_observer in dev mode to
	# more easily pass in specific files we need, such as creds
	${PIP} install --no-cache-dir -e learning_observer/[${PACKAGES}]
	# TODO resolve the lodrc-current symlink and fetch that url instead
	@LODRC_CURRENT=$$(curl -s https://raw.githubusercontent.com/ETS-Next-Gen/lo_assets/main/lo_dash_react_components/lo_dash_react_components-current.tar.gz); \
	${PIP} install https://raw.githubusercontent.com/ETS-Next-Gen/lo_assets/main/lo_dash_react_components/$${LODRC_CURRENT}
	${PIP} install ollama

install-dev: venv
	# TODO create a dev requirements file
	${PIP} install --no-cache-dir -e learning_observer/[${PACKAGES}]
	. ${HOME}/.nvm/nvm.sh && nvm use && ${PIP} install -v -e modules/lo_dash_react_components/
	${PIP} install ollama

# testing commands
test:
	# this is where we run doctests
	pytest modules/wo_highlight_dashboard

# Linting commands
linting-python:
	# Linting Python modules
	${PIP} install pycodestyle
	pycodestyle --ignore=E501,W503 $$(git ls-files 'learning_observer/*.py' 'modules/*.py')

linting-node:
	# TODO each of these have lots of errors and block
	# the next item from running
	# Starting to lint Node modules
	npm install
	# Linting Javascript
	npm run lint:js
	# Linting CSS
	npm run lint:css
	# Finding any unused CSS files
	npm run find-unused-css

linting: linting-python
	# Finished linting
