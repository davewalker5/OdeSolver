import os
import pytest
from src.ode_solver.utils.function_loader import load_module_from_file, get_function_from_module


@pytest.fixture()
def module_path():
    tests_folder = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    module_path = os.path.join(tests_folder, "data", "example_function_1.py")
    return module_path


def test_module_loader(module_path):
    module = load_module_from_file(module_path, "function_to_solve")
    function = get_function_from_module(module, "f")
    value = function(2, 8)
    assert 4 == value
