import os
import pytest
from ode_solver import Euler, load_function_from_file


@pytest.fixture()
def function():
    tests_folder = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    module_path = os.path.join(tests_folder, "data", "example_function.py")
    f = load_function_from_file(module_path, "function_to_solve", "f")
    return f


@pytest.fixture()
def expected_solution():
    return [
        {
            "method": "Euler",
            "step": 0,
            "t": "0.0",
            "y": "0.5",
            "step_size": "0.5",
            "difference": 0,
            "tolerance": "0"
        },
        {
            "method": "Euler",
            "step": 1,
            "t": "0.5",
            "y": "0.625",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "Euler",
            "step": 2,
            "t": "1.0",
            "y": "0.78125",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "Euler",
            "step": 3,
            "t": "1.5",
            "y": "0.976562",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "Euler",
            "step": 4,
            "t": "2.0",
            "y": "1.22070",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "Euler",
            "step": 5,
            "t": "2.5",
            "y": "1.52588",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "Euler",
            "step": 6,
            "t": "3.0",
            "y": "1.90735",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "Euler",
            "step": 7,
            "t": "3.5",
            "y": "2.38419",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "Euler",
            "step": 8,
            "t": "4.0",
            "y": "2.98024",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "Euler",
            "step": 9,
            "t": "4.5",
            "y": "3.72530",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "Euler",
            "step": 10,
            "t": "5.0",
            "y": "4.65662",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        }
    ]


def test_euler_solution(function, expected_solution):
    e = Euler(function, None, 6)
    e.solve_for_steps(10, 0.5, 0.5)

    assert len(expected_solution) == len(e.history)
    for i, point in enumerate(expected_solution):
        assert point["step"] == e.history[i]["step"]
        assert point["t"] == str(e.history[i]["t"])
        assert point["y"] == str(e.history[i]["y"])
