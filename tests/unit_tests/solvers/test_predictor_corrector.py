import os
import pytest
from ode_solver import PredictorCorrector, load_function_from_file


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
            "method": "PredictorCorrector",
            "step": 0,
            "t": "0.0",
            "y": "0.5",
            "step_size": "0.5",
            "difference": 0,
            "tolerance": "0"
        },
        {
            "method": "PredictorCorrector",
            "step": 1,
            "t": "0.5",
            "y": "0.640625",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "PredictorCorrector",
            "step": 2,
            "t": "1.0",
            "y": "0.820801",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "PredictorCorrector",
            "step": 3,
            "t": "1.5",
            "y": "1.05165",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "PredictorCorrector",
            "step": 4,
            "t": "2.0",
            "y": "1.34742",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "PredictorCorrector",
            "step": 5,
            "t": "2.5",
            "y": "1.72638",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "PredictorCorrector",
            "step": 6,
            "t": "3.0",
            "y": "2.21192",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "PredictorCorrector",
            "step": 7,
            "t": "3.5",
            "y": "2.83402",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "PredictorCorrector",
            "step": 8,
            "t": "4.0",
            "y": "3.63109",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "PredictorCorrector",
            "step": 9,
            "t": "4.5",
            "y": "4.65233",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "PredictorCorrector",
            "step": 10,
            "t": "5.0",
            "y": "5.96079",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        }
    ]


def test_predictor_corrector_solution(function, expected_solution):
    pc = PredictorCorrector(function, None, 6)
    pc.solve_for_steps(10, 0.5, 0.5)

    assert len(expected_solution) == len(pc.history)
    for i, point in enumerate(expected_solution):
        assert point["step"] == pc.history[i]["step"]
        assert point["t"] == str(pc.history[i]["t"])
        assert point["y"] == str(pc.history[i]["y"])
