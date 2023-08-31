import learning_observer.test_utils
import wo_highlight_dashboard.module as unit


def test_module_loaded():
    learning_observer.test_utils.check_integration(unit, 'wo_highlight_dashboard')
