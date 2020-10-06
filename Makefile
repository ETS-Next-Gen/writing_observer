# Build browser extension

extension-package:
	google-chrome --pack-extension=extension --pack-extension-key=extension.pem --disable-setuid-sandbox --no-gpu --no-sandbox --headless
