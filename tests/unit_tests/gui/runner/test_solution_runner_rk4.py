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
        "method": "4th-Order Runge-Kutta",
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
            "y": "1.42513",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "RungeKutta4",
            "step": 2,
            "t": "1.0",
            "y": "2.63960",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "RungeKutta4",
            "step": 3,
            "t": "1.5",
            "y": "4.00682",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "RungeKutta4",
            "step": 4,
            "t": "2.0",
            "y": "5.30160",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "RungeKutta4",
            "step": 5,
            "t": "2.5",
            "y": "6.15277",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "RungeKutta4",
            "step": 6,
            "t": "3.0",
            "y": "5.94845",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "RungeKutta4",
            "step": 7,
            "t": "3.5",
            "y": "3.68000",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "RungeKutta4",
            "step": 8,
            "t": "4.0",
            "y": "-2.31525",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "RungeKutta4",
            "step": 9,
            "t": "4.5",
            "y": "-14.7782",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "RungeKutta4",
            "step": 10,
            "t": "5.0",
            "y": "-38.2267",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        },
        {
            "method": "RungeKutta4",
            "step": 11,
            "t": "5.5",
            "y": "-80.1087",
            "step_size": "0.5",
            "difference": "0",
            "tolerance": "0"
        }
    ]


def test_can_run_solution_using_rk4_method(simulation_options, expected_results):
    window = MockWindow(None)
    chart = MockChart()
    table = MockDataTable()

    runner = SolutionRunner(chart, table, window)
    runner.run(simulation_options)

    assert len(expected_results) == len(runner.history)
    for i, result in enumerate(expected_results):
        assert "RungeKutta4" == runner.history[i]["method"]
        assert Decimal(result["t"]) == runner.history[i]["t"]
        assert Decimal(result["y"]) == runner.history[i]["y"]
