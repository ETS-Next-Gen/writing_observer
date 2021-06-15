PYTHONFILES = $(wildcard \
	learning_observer/learning_observer/*py \
	learning_observer/util/*py \
	gitserve/gitserve/*py \
	gitserve/*py \
	learning_observer/learning_observer/pubsub/*py \
	learning_observer/learning_observer/stream_analytics/*py \
)

run:
	# If you haven't done so yet, run: make install
	# Also, run: workon learning_observer
	cd learning_observer && python learning_observer

# Build browser extension
extension-package:
	# I won't build this for you, but I will give you instructions, since
	# the set of options will vary.
	#
	# On my last system, I needed:
	#	google-chrome --pack-extension=extension --pack-extension-key=extension.pem --disable-setuid-sandbox --no-gpu --no-sandbox --headless
	# On my current system
	#	google-chrome --pack-extension=extension --pack-extension-key=extension.pem
	# The pem file is your private key. You'll need to make one.
	# The output will be called extension.crx

codestyle:
	# Check code style quality
	#
	# In pycodestyle, we ignore E501 (line too long) and W503 (which
	# requires a choice.
        # https://stackoverflow.com/questions/57074300/what-is-the-recommended-way-to-break-long-if-statement-w504-line-break-after-b
	#
	# In pylint, we ignore:
	# 1. W0613: unused arguments (common for e.g. `request` parameter)
	# 2. E501/C0301: line too long (obsolete with modern computers
	#    ref: https://lkml.org/lkml/2020/5/29/1038)
	#    We still aim for shorter lines, but it's not a showstopper if
	#    we break the limit occasionally. We may re-examine this decision
	#    if we have sufficient developers working on VT100 terminals.
	# 3. W0511: TODO: We're gonna have a lot of these, and we want to
	#    encourage leaving these around. As a coding style, we want to
	#    get interface and overall structures right, and then clean
	#    up e.g. performance/scaling, exception handling, test coverage,
	#    etc. once we know what we're doing.
	# 4. R0913: Too many arguments. That's a relic of web apps. Sorry.
	#
	# Generally, pycodestyle issues are showstopppers for pushing to
	# upstream. Pylint issues are worth an occasional cleanup pass, but we
	# can tolerate.

	pycodestyle --ignore=E501,W503 $(PYTHONFILES)
	pylint -d W0613,W0511,C0301,R0913,too-few-public-methods $(PYTHONFILES)

install:
	# Run:
	#    mkvirtualenv learning_observer
	#    pip install -r requirements.txt
	#    cd learning_observer
	#    python setup.py develop
	#    python learning_observer
	# And then clean up this Makefile to do it for you automatically :)

sphinx:
	cd learning_observer/docs; make html
