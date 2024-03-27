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

test:
	# this is where we run doctests

linting:
	# we ought to handle linting at this level
	# we should combine both the old and whatever else I did

sphinx:
	# this is where we build our sphinx doctests
