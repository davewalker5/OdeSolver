import os
import pytest
from ode_solver import RungeKutta4, load_function_from_file


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
            "method": "RungeKutta4",
            "step": 0,
            "t": "0.0",
            "y": "0.5",
            "step_size": "0.5",
            "difference": 0,
            "tolerance": "0"
        },
        {
            "method": "RungeKutta4",
            "step": 1,
            "t": "0.5",
            "y": "0.642008",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "RungeKutta4",
            "step": 2,
            "t": "1.0",
            "y": "0.824350",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "RungeKutta4",
            "step": 3,
            "t": "1.5",
            "y": "1.05848",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "RungeKutta4",
            "step": 4,
            "t": "2.0",
            "y": "1.35911",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "RungeKutta4",
            "step": 5,
            "t": "2.5",
            "y": "1.74512",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "RungeKutta4",
            "step": 6,
            "t": "3.0",
            "y": "2.24076",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "RungeKutta4",
            "step": 7,
            "t": "3.5",
            "y": "2.87718",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "RungeKutta4",
            "step": 8,
            "t": "4.0",
            "y": "3.69435",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "RungeKutta4",
            "step": 9,
            "t": "4.5",
            "y": "4.74361",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "RungeKutta4",
            "step": 10,
            "t": "5.0",
            "y": "6.09087",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        }
    ]


def test_rk4_solution(function, expected_solution):
    rk4 = RungeKutta4(function, None, 6)
    rk4.solve_for_steps(10, 0.5, 0.5)

    assert len(expected_solution) == len(rk4.history)
    for i, point in enumerate(expected_solution):
        assert point["step"] == rk4.history[i]["step"]
        assert point["t"] == str(rk4.history[i]["t"])
        assert point["y"] == str(rk4.history[i]["y"])
