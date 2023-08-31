import learning_observer.test_utils
import writing_observer.module as unit


def test_module_loaded():
    learning_observer.test_utils.check_integration(unit, 'writing_observer')
