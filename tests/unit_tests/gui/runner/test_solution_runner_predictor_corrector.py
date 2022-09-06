import pytest
from decimal import Decimal
from tests.mocks import MockWindow, MockChart, MockDataTable
from ode_solver.gui.runner import SolutionRunner
from tests.unit_tests.gui.runner.runner_test_helpers import load_function_definition


@pytest.fixture()
def simulation_options():
    return {
        "function": load_function_definition("example_function_2.py"),
        "method": "Predictor-Corrector",
        "limit": "5",
        "steps": "",
        "step_size": "0.5",
        "initial_value": "0.5",
        "tolerance": "",
        "adjust_step_size": False,
        "chart_title": "dy/dx = y - t^2 + 1",
        "chart_min_y": "-100",
        "chart_max_y": "20",
        "chart_max_x": "6",
        "chart_auto_scale": False
    }


@pytest.fixture()
def expected_results():
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
            "y": "1.3750",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "PredictorCorrector",
            "step": 2,
            "t": "1.0",
            "y": "2.51562",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "PredictorCorrector",
            "step": 3,
            "t": "1.5",
            "y": "3.77538",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "PredictorCorrector",
            "step": 4,
            "t": "2.0",
            "y": "4.91624",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "PredictorCorrector",
            "step": 5,
            "t": "2.5",
            "y": "5.55139",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "PredictorCorrector",
            "step": 6,
            "t": "3.0",
            "y": "5.05226",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "PredictorCorrector",
            "step": 7,
            "t": "3.5",
            "y": "2.39741",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "PredictorCorrector",
            "step": 8,
            "t": "4.0",
            "y": "-4.07299",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "PredictorCorrector",
            "step": 9,
            "t": "4.5",
            "y": "-17.0561",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "PredictorCorrector",
            "step": 10,
            "t": "5.0",
            "y": "-40.9349",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "PredictorCorrector",
            "step": 11,
            "t": "5.5",
            "y": "-82.8317",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        }
    ]


def test_can_run_solution_using_predictor_corrector_method(simulation_options, expected_results):
    window = MockWindow(None)
    chart = MockChart()
    table = MockDataTable()

    runner = SolutionRunner(chart, table, window)
    runner.run(simulation_options)

    assert len(expected_results) == len(runner.history)
    for i, result in enumerate(expected_results):
        assert "PredictorCorrector" == runner.history[i]["method"]
        assert Decimal(result["t"]) == runner.history[i]["t"]
        assert Decimal(result["y"]) == runner.history[i]["y"]
