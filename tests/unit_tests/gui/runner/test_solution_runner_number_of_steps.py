import os
import pytest
from decimal import Decimal
from tests.mocks import MockWindow, MockChart, MockDataTable
from ode_solver.gui.runner import SolutionRunner


@pytest.fixture()
def simulation_options():
    tests_folder = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    function_file = os.path.join(tests_folder, "data", "example_function_2.py")
    return {
        "function_file": function_file,
        "method": "Euler",
        "limit": "",
        "steps": "5",
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
            "y": "1.250",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "Euler",
            "step": 2,
            "t": "1.0",
            "y": "2.2500",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "Euler",
            "step": 3,
            "t": "1.5",
            "y": "3.37500",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "Euler",
            "step": 4,
            "t": "2.0",
            "y": "4.43750",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "Euler",
            "step": 5,
            "t": "2.5",
            "y": "5.15625",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        }
    ]


def test_can_run_solution_using_fixed_number_of_steps(simulation_options, expected_results):
    window = MockWindow(None)
    chart = MockChart()
    table = MockDataTable()

    runner = SolutionRunner(chart, table, window)
    runner.run(simulation_options)

    assert len(expected_results) == len(runner.history)
    for i, result in enumerate(expected_results):
        assert "Euler" == runner.history[i]["method"]
        assert Decimal(result["t"]) == runner.history[i]["t"]
        assert Decimal(result["y"]) == runner.history[i]["y"]
