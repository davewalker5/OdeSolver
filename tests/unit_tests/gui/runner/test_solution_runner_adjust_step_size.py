import os
import pytest
from ode_solver import RungeKutta4, load_function_from_file


@pytest.fixture()
def function():
    tests_folder = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
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
            "tolerance": "0.01"
        },
        {
            "method": "RungeKutta4",
            "step": 1,
            "t": "0.75",
            "y": "0.727463",
            "step_size": "0.75",
            "difference": "0.000030",
            "tolerance": "0.01"
        },
        {
            "method": "RungeKutta4",
            "step": 2,
            "t": "1.875",
            "y": "1.27636",
            "step_size": "1.125",
            "difference": "0.00035",
            "tolerance": "0.01"
        },
        {
            "method": "RungeKutta4",
            "step": 3,
            "t": "3.5625",
            "y": "2.96234",
            "step_size": "1.6875",
            "difference": "0.00482",
            "tolerance": "0.01"
        },
        {
            "method": "RungeKutta4",
            "step": 4,
            "t": "4.82812",
            "y": "5.57499",
            "step_size": "1.26562",
            "difference": "0.00256",
            "tolerance": "0.01"
        },
        {
            "method": "RungeKutta4",
            "step": 5,
            "t": "5.77734",
            "y": "8.95992",
            "step_size": "0.949215",
            "difference": "0.00114",
            "tolerance": "0.01"
        },
        {
            "method": "RungeKutta4",
            "step": 6,
            "t": "6.48925",
            "y": "12.7902",
            "step_size": "0.71191",
            "difference": "0.0005",
            "tolerance": "0.01"
        },
        {
            "method": "RungeKutta4",
            "step": 7,
            "t": "7.55711",
            "y": "21.8102",
            "step_size": "1.06786",
            "difference": "0.0047",
            "tolerance": "0.01"
        },
        {
            "method": "RungeKutta4",
            "step": 8,
            "t": "8.35800",
            "y": "32.5496",
            "step_size": "0.800895",
            "difference": "0.0018",
            "tolerance": "0.01"
        },
        {
            "method": "RungeKutta4",
            "step": 9,
            "t": "8.95867",
            "y": "43.9514",
            "step_size": "0.60067",
            "difference": "0.0007",
            "tolerance": "0.01"
        },
        {
            "method": "RungeKutta4",
            "step": 10,
            "t": "9.85968",
            "y": "68.9569",
            "step_size": "0.901005",
            "difference": "0.0066",
            "tolerance": "0.01"
        },
        {
            "method": "RungeKutta4",
            "step": 11,
            "t": "10.5354",
            "y": "96.6727",
            "step_size": "0.675755",
            "difference": "0.0026",
            "tolerance": "0.01"
        },
        {
            "method": "RungeKutta4",
            "step": 12,
            "t": "11.0422",
            "y": "124.553",
            "step_size": "0.506815",
            "difference": "0.001",
            "tolerance": "0.01"
        },
        {
            "method": "RungeKutta4",
            "step": 13,
            "t": "11.8024",
            "y": "182.143",
            "step_size": "0.760222",
            "difference": "0.009",
            "tolerance": "0.01"
        },
        {
            "method": "RungeKutta4",
            "step": 14,
            "t": "12.3726",
            "y": "242.224",
            "step_size": "0.570165",
            "difference": "0.002",
            "tolerance": "0.01"
        },
        {
            "method": "RungeKutta4",
            "step": 15,
            "t": "12.8002",
            "y": "299.967",
            "step_size": "0.427624",
            "difference": "0.001",
            "tolerance": "0.01"
        },
        {
            "method": "RungeKutta4",
            "step": 16,
            "t": "13.4416",
            "y": "413.381",
            "step_size": "0.641436",
            "difference": "0.008",
            "tolerance": "0.01"
        },
        {
            "method": "RungeKutta4",
            "step": 17,
            "t": "13.9227",
            "y": "525.790",
            "step_size": "0.481077",
            "difference": "0.003",
            "tolerance": "0.01"
        },
        {
            "method": "RungeKutta4",
            "step": 18,
            "t": "14.2835",
            "y": "629.738",
            "step_size": "0.360808",
            "difference": "0.001",
            "tolerance": "0.01"
        },
        {
            "method": "RungeKutta4",
            "step": 19,
            "t": "14.8247",
            "y": "825.426",
            "step_size": "0.541212",
            "difference": "0.007",
            "tolerance": "0.01"
        },
        {
            "method": "RungeKutta4",
            "step": 20,
            "t": "15.2306",
            "y": "1011.16",
            "step_size": "0.405909",
            "difference": "0.00",
            "tolerance": "0.01"
        },
        {
            "method": "RungeKutta4",
            "step": 21,
            "t": "15.5350",
            "y": "1177.41",
            "step_size": "0.304432",
            "difference": "0.01",
            "tolerance": "0.01"
        },
        {
            "method": "RungeKutta4",
            "step": 22,
            "t": "15.9916",
            "y": "1479.40",
            "step_size": "0.456648",
            "difference": "0.01",
            "tolerance": "0.01"
        },
        {
            "method": "RungeKutta4",
            "step": 23,
            "t": "16.3341",
            "y": "1755.72",
            "step_size": "0.342486",
            "difference": "0.00",
            "tolerance": "0.01"
        },
        {
            "method": "RungeKutta4",
            "step": 24,
            "t": "16.5910",
            "y": "1996.33",
            "step_size": "0.256864",
            "difference": "0.00",
            "tolerance": "0.01"
        },
        {
            "method": "RungeKutta4",
            "step": 25,
            "t": "16.9763",
            "y": "2420.46",
            "step_size": "0.385296",
            "difference": "0.00",
            "tolerance": "0.01"
        },
        {
            "method": "RungeKutta4",
            "step": 26,
            "t": "17.2653",
            "y": "2796.71",
            "step_size": "0.288972",
            "difference": "0.00",
            "tolerance": "0.01"
        },
        {
            "method": "RungeKutta4",
            "step": 27,
            "t": "17.6988",
            "y": "3473.52",
            "step_size": "0.433458",
            "difference": "0.01",
            "tolerance": "0.01"
        },
        {
            "method": "RungeKutta4",
            "step": 28,
            "t": "17.8613",
            "y": "3767.62",
            "step_size": "0.162547",
            "difference": "0.01",
            "tolerance": "0.01"
        },
        {
            "method": "RungeKutta4",
            "step": 29,
            "t": "18.1051",
            "y": "4256.10",
            "step_size": "0.243820",
            "difference": "0.00",
            "tolerance": "0.01"
        },
        {
            "method": "RungeKutta4",
            "step": 30,
            "t": "18.4708",
            "y": "5110.09",
            "step_size": "0.365730",
            "difference": "0.01",
            "tolerance": "0.01"
        },
        {
            "method": "RungeKutta4",
            "step": 31,
            "t": "18.7451",
            "y": "5861.27",
            "step_size": "0.274298",
            "difference": "0.00",
            "tolerance": "0.01"
        },
        {
            "method": "RungeKutta4",
            "step": 32,
            "t": "18.9508",
            "y": "6496.27",
            "step_size": "0.205724",
            "difference": "0.00",
            "tolerance": "0.01"
        },
        {
            "method": "RungeKutta4",
            "step": 33,
            "t": "19.2594",
            "y": "7580.06",
            "step_size": "0.308586",
            "difference": "0.00",
            "tolerance": "0.01"
        },
        {
            "method": "RungeKutta4",
            "step": 34,
            "t": "19.4908",
            "y": "8509.99",
            "step_size": "0.231440",
            "difference": "0.01",
            "tolerance": "0.01"
        },
        {
            "method": "RungeKutta4",
            "step": 35,
            "t": "19.8380",
            "y": "10123.1",
            "step_size": "0.347160",
            "difference": "0.0",
            "tolerance": "0.01"
        },
        {
            "method": "RungeKutta4",
            "step": 36,
            "t": "19.9682",
            "y": "10804.0",
            "step_size": "0.130185",
            "difference": "0.0",
            "tolerance": "0.01"
        },
        {
            "method": "RungeKutta4",
            "step": 37,
            "t": "20.1635",
            "y": "11912.1",
            "step_size": "0.195278",
            "difference": "0.0",
            "tolerance": "0.01"
        }
    ]


def test_solution_runner_adjusting_step_size(function, expected_solution):
    e = RungeKutta4(function, None, 6)
    e.solve_for_range(20, 0.5, 0.5, True, 0.01)

    assert len(expected_solution) == len(e.history)
    for i, point in enumerate(expected_solution):
        assert point["step"] == e.history[i]["step"]
        assert point["t"] == str(e.history[i]["t"])
        assert point["y"] == str(e.history[i]["y"])
