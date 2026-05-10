import tempfile
import os
import subprocess
from pathlib import Path
from typing import Any
from seasonal.support.utils import D
from seasonal.support.json import load_simulated_json, write_json


def _run_solver(solver_command: str, params_file: str, simulation_file: str, output_file: str, chart_file: str):
    """
    Run the ODE Solver

    :param solver_command: ODE Solver command
    :param params_file: Path to the simulation parameters file
    :param simulation_file: Path to the simulation JSON
    :param output_file: Path to the simulated output CSV file
    :param chart_file: Path to the simulated chart PNG file
    """
    # Set the environment variable to point to the model parameter file
    env = os.environ.copy()
    env["SEASONAL_PARAMS_FILE"] = str(params_file)

    # Construct the arguments
    arguments = [
        solver_command,
        "--simulation", str(simulation_file),
        "--quiet",
        "--no-gui",
        "--export", str(output_file),
    ]

    # If a chart has been specified, add it to the arguments
    if chart_file:
        arguments = arguments + ["--chart", str(chart_file)]

    # Run the ODE Solver
    subprocess.run(arguments, check=True, env=env)


def monthly_average(points: list, discard_months: Any = D("0")) -> dict:
    """
    Convert solver output points into monthly bins.

    t = 0.0..0.999 -> month 1
    t = 1.0..1.999 -> month 2
    ...
    t = 11.0..11.999 -> month 12

    If discard_months is supplied, the initial portion of the simulation is
    ignored before binning. This can be useful if the simulation is run with
    a warm-up period.

    :param points: List of solution points
    :param discard_months: Number of initial simulation months to discard
    :return: Dictionary of monthly averaged values
    """
    bins = {m: [] for m in range(1, 13)}
    discard_months = D(discard_months)

    for p in points:
        t = p["t"]

        if t < discard_months:
            continue

        adjusted_t = t - discard_months
        month = int(adjusted_t % D("12")) + 1

        if 1 <= month <= 12:
            bins[month].append(p["y"])

    return {
        month: sum(values) / len(values)
        for month, values in bins.items()
        if values
    }


def run_solver(simulation_file: str, params: dict, solver_command: str, discard_months: Any = D("0")) -> dict:
    """
    Run ODE Solver with a temporary parameter file.

    :param simulation_file: Path to the simulation JSON
    :param params: Parameter dictionary
    :param solver_command: ODE Solver command
    :param discard_months: Initial months to discard when binning
    :return: Monthly simulated values
    """
    with tempfile.TemporaryDirectory() as tmp:
        # Construct the parameter file path and output JSON file path
        tmp = Path(tmp)
        params_file = tmp / "resident_params.json"
        output_file = tmp / "output.json"

        # Write the parameters to the model parameter file
        solver_params = {k: v for k, v in params.items() if k != "SCALE"}
        write_json(params_file, solver_params)

        # Run the ODE Solver
        _run_solver(solver_command, params_file, simulation_file, output_file, None)

        points = load_simulated_json(output_file)
        return monthly_average(points, discard_months=discard_months)


def export_simulation(solver_command: str, params_file: str, simulation_file: str, output_file: str, chart_file: str):
    """
    Run the ODE Solver

    :param solver_command: ODE Solver command
    :param params_file: Path to the simulation parameters file
    :param simulation_file: Path to the simulation JSON
    :param output_file: Path to the simulated output CSV file
    :param chart_file: Path to the simulated chart PNG file
    """
    _run_solver(solver_command, params_file, simulation_file, output_file, chart_file)
