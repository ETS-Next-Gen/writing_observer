# Build browser extension

extension-package:
	google-chrome --pack-extension=extension --pack-extension-key=extension.pem --disable-setuid-sandbox --no-gpu --no-sandbox --headless

codestyle:
	# Check code style quality
	#
	# We should add more directories!
	#
	# We ignore:
	# 1. unused arguments (common for `request` parameter)
	# 2. line too long (modern computers)
	# 3. TODO (we use these longitudonally, to show code trajectory)
	# We still aim for shorter lines, but it's not a showstopper if we break
	# 80 chars sometimes.
	pycodestyle --ignore=E501 learning_observer/learning_observer/*py
	pylint -d W0613,W0511,C0301 learning_observer/learning_observer/*py
