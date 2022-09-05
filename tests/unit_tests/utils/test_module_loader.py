import os
import pytest
from ode_solver import load_function_from_file


@pytest.fixture()
def module_path():
    tests_folder = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    module_path = os.path.join(tests_folder, "data", "example_function.py")
    return module_path


def test_module_loader(module_path):
    function = load_function_from_file(module_path, "function_to_solve", "f")
    value = function(2, 8)
    assert 4 == value
