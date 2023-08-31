import learning_observer.offline


def pytest_configure():
    learning_observer.offline.init()
