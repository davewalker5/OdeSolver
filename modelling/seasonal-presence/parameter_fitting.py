import argparse
import csv
import json
import os
import random
import subprocess
import tempfile
from decimal import Decimal
from pathlib import Path


def D(value):
    """
    Safely convert a value to a Decimal

    :param value: Value to convert
    :return: The Decimal conversion of that value
    """
    return Decimal(str(value))


def load_observed_csv(path):
    """
    Load the observed data and normalise it, mapping it into the range 0 to 1.0. The
    CSV file is expected to have:

    - A "month" column containing the month number
    - A "value" column containing the presence score or raw count
    - 12 records, one for each month (1 to 12)

    :param path: Path to the CSV file to load
    :return: Normalised observed data
    """

    # Load the observed data
    rows = {}

    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            month = int(row["month"])
            value = D(row["value"])
            rows[month] = value

    # Calculate the maximum
    max_value = max(rows.values())

    # If the data is flat, at 0.0, avoid divide-by-zero and return a "zero" data set
    if max_value == 0:
        return {m: D("0") for m in rows}

    # Normalise the data
    return {
        month: value / max_value
        for month, value in rows.items()
    }


def load_simulated_json(path):
    """
    Load the JSON format simulation output

    :param path: Path to the simulation output file
    :return: A list of dictionaries, each representing a point (t, y)
    """

    # Load the data
    with open(path) as f:
        data = json.load(f)

    # Compile a list of points in which y is the normalised value, if present, or the
    # non-normalised value if not
    points = []
    for p in data:
        y_key = "y_normalised" if "y_normalised" in p else "y"

        points.append({
            "t": D(p["t"]),
            "y": D(p[y_key]),
        })

    return points


def monthly_average(points):
    """
    Converts the points representing the solution into monthly bins

    t = 0.0..0.999 -> month 1
    t = 1.0..1.999 -> month 2
    ...
    t = 11.0..11.999 -> month 12

    :param points: List of dictionaries, each representing a point in the solution
    :return: A dictionary of values binned by month
    """

    bins = {m: [] for m in range(1, 13)}

    for p in points:
        month = int(p["t"]) + 1

        if 1 <= month <= 12:
            bins[month].append(p["y"])

    return {
        month: sum(values) / len(values)
        for month, values in bins.items()
        if values
    }


def mse(observed, simulated):
    """
    Calculate the mean squared error (MSE) between observed and simulated data

    MSE = (1 / N) * Σ (observed - simulated)²

    :param observed: Dictionary of observed data points
    :param simulated: Dictionary of simulated data points
    :return: MSE
    """
    # Get a list of months that appear in both the observed and simulated data
    months = sorted(set(observed) & set(simulated))
    if not months:
        raise ValueError("No overlapping months between observed and simulated data")

    # For each month, the error is calculated as the squared difference between observed
    # and simulated data. This is summed to give the mismatch across the year and then
    # divided by the number of months to give a monthly average mismatch
    return sum((observed[m] - simulated[m]) ** 2 for m in months) / D(len(months))


def weighted_score(observed, simulated):
    """
    Combine the following error components to produce a single weighted error score:

    - Curve fit error
    - Peak month error
    - First/last active month error

    :param observed: Dictionary of observed data points
    :param simulated: Dictionary of simulated data points
    :return: Weighted error score
    """

    # Calculate the MSE across the curve
    curve_error = mse(observed, simulated)

    # Determing the observed and simulated peaks and calculate the peak error
    observed_peak = max(observed, key=observed.get)
    simulated_peak = max(simulated, key=simulated.get)
    peak_error = D(abs(observed_peak - simulated_peak)) / D("12")

    # Determine the observed and active months
    observed_active = [m for m, v in observed.items() if v > D("0.05")]
    simulated_active = [m for m, v in simulated.items() if v > D("0.05")]

    if observed_active and simulated_active:
        # Determine errors in the positioning of the peaks
        start_error = D(abs(min(observed_active) - min(simulated_active))) / D("12")
        end_error = D(abs(max(observed_active) - max(simulated_active))) / D("12")
    else:
        start_error = D("1")
        end_error = D("1")

    # Calculate a weighted sum of the error components. Errors in the shape of the curve
    # have a weighting of 1.0, other components of 0.25. This cares most about the shape
    # of the curve but does penalise if the seasonality is wrong
    return curve_error + D("0.25") * peak_error + D("0.25") * start_error + D("0.25") * end_error


def run_solver(simulation_file, params, solver_command):
    """
    Run the solution with the current set of parameters
    
    :param simulation_file: Path to the ODE Solver simulation file
    :param params: Dictionary of seasonal presence parameters
    :param solver_command: Command used to run the ODE Solver
    :return: A dictionary of values binned by month
    """
    with tempfile.TemporaryDirectory() as tmp:
        # Generate the file path
        tmp = Path(tmp)
        params_file = tmp / "seasonal_params.json"
        output_file = tmp / "output.json"

        # Write the parameters to a temporary JSON file
        params_file.write_text(json.dumps(params, indent=2))

        # Set the environment variable that points to the parameters file.
        # The parameters are loaded from there by the code in the simulation
        # file
        env = os.environ.copy()
        env["SEASONAL_PARAMS_FILE"] = str(params_file)

        # Run the ODE Solver
        subprocess.run(
            [
                solver_command,
                "-s", str(simulation_file),
                "-q",
                "-ng",
                "-e", str(output_file),
            ],
            check=True,
            env=env,
        )

        # Load the JSON output by the ODE solver
        points = load_simulated_json(output_file)

        # Conver the points to monthly bins
        return monthly_average(points)


def make_random_params():
    """
    Generate a random set of parameters for the seasonal model

    :return: Dictionary of parameter values
    """
    season_start = round(random.uniform(2.0, 7.0), 2)
    season_end = round(random.uniform(season_start + 1.0, 11.5), 2)

    return {
        "GROWTH": "2.0",
        "DECAY": "1.5",
        "OOS_DECAY": "3.0",
        "SEASON_START": str(season_start),
        "SEASON_END": str(season_end),
        "SHARPNESS": str(round(random.uniform(0.5, 8.0), 3)),
        "FORCING_PEAK": str(round(random.uniform(1.0, 12.0), 2)),
    }


def fit(observed, simulation_file, iterations, solver_command):
    """
    Parameter fitting loop
    
    :param observed: Observed behaviour being matched
    :param simulation_file: Path to the ODE Solver simulation file
    :param iterations: Number of iterations in the fit
    :param solver_command: Command used to run the ODE Solver
    :return: A dictionary of parameters yielding the best fit
    """
    best = None

    # Iterate the specified number of times
    for i in range(iterations):
        # Generate a random parameter ste
        params = make_random_params()

        try:
            # Run the simulation and 
            simulated = run_solver(simulation_file, params, solver_command)
            score = weighted_score(observed, simulated)

        except Exception as e:
            print(f"Trial {i + 1}: failed: {e}")
            continue

        # If this is the best fit so far, capture it
        if best is None or score < best["score"]:
            best = {
                "score": score,
                "params": params,
                "simulated": simulated,
            }

            print()
            print(f"New best at trial {i + 1}")
            print(f"Score: {score}")
            print(json.dumps(params, indent=2))

    return best


def main():
    """
    Main entry point for the seasonal presence parameter fitter
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("-o", "--observed", required=True, help="CSV file containing month,value columns")
    parser.add_argument("-s", "--simulation", required=True, help="Simulation JSON file for ODE Solver")
    parser.add_argument("-i", "--iterations", type=int, default=200, help="Number of parameter sets to test")
    parser.add_argument("-sc", "--solver-command", help="ODE Solver command")
    parser.add_argument("-b", "--best-output", default="best_params.json", help="Where to write the best parameter file")
    args = parser.parse_args()

    observed = load_observed_csv(args.observed)

    best = fit(observed, Path(args.simulation), args.iterations, args.solver_command)

    if best is None:
        raise RuntimeError("No successful parameter set found")

    Path(args.best_output).write_text(json.dumps(best["params"], indent=2))

    print()
    print("Best fit")
    print("--------")
    print(f"Score: {best['score']}")
    print(json.dumps(best["params"], indent=2))
    print()
    print(f"Wrote: {args.best_output}")


if __name__ == "__main__":
    main()
