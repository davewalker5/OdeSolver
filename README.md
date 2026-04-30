[![Build Status](https://github.com/davewalker5/OdeSolver/workflows/Python%20CI%20Build/badge.svg)](https://github.com/davewalker5/OdeSolver/actions)
[![Coverage](https://codecov.io/gh/davewalker5/OdeSolver/branch/main/graph/badge.svg?token=U86UFDVD5S)](https://codecov.io/gh/davewalker5/OdeSolver)
[![GitHub issues](https://img.shields.io/github/issues/davewalker5/OdeSolver)](https://github.com/davewalker5/OdeSolver/issues)
[![Releases](https://img.shields.io/github/v/release/davewalker5/OdeSolver.svg?include_prereleases)](https://github.com/davewalker5/OdeSolver/releases)
[![License](https://img.shields.io/badge/License-mit-blue.svg)](https://github.com/davewalker5/OdeSolver/blob/main/LICENSE)
[![Language](https://img.shields.io/badge/language-python-blue.svg)](https://www.python.org)
[![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/davewalker5/OdeSolver)](https://github.com/davewalker5/OdeSolver/)

# OdeSolver

Ordinary Differential Equation Solver

# Structure

| Package            | Contents                                                      |
| ------------------ | ------------------------------------------------------------- |
| ode_solver.cli     | Command line parser and "headless" entry-point                |
| ode_solver.gui     | Implementation of a desktop user interface                    |
| ode_solver.options | Simulation options management and storage                     |
| ode_solver.solvers | Implementation of the integration methods and solution runner |
| ode_solver.utils   | Supporting utilities for the integration methods and data I/O |

# Running the Application

## Pre-requisites

To run the application, a virtual environment should be created, the requirements should be installed using pip and the environment should be activated.

## Running the Desktop Application

The application can then be run from the command line, at the root of
the project folder, as follows:

```bash
export PYTHONPATH=`pwd`/src/
python -m ode_solver
```

The first command adds the source folder, containing the application source, to the PYTHONPATH environment variable so the packages will be found at run time. The command will need to be modified based on the current operating system.

When the application starts, a window similar to the following will be displayed, though it will not contain a chart until solution options have been set and the solution has been run:

![ODE Solver Main Window](https://github.com/davewalker5/OdeSolver/blob/main/docs/images/chart_tab.png?raw=true){width="400px"}

## Command Line Options

The following table summarises the command line options supported by theODE Solver:

| Option       | Short Form | Context | Description                                                                            |
| ------------ | ---------- | ------- | -------------------------------------------------------------------------------------- |
| --simulation | -s         | All     | Specify a JSON-format simulation options file to load on startup                       |
| --export     | -e         | All     | Specify the path to a CSV, JSON or XML export file to export the data to on completion |
| --chart      | -c         | All     | Specify the path to a PNG file to export the simulation chart to on completion         |
| --auto-run   | -ar        | GUI     | Automatically start the simulation specified using --simulation on startup             |
| --no-gui     | -ng        | CLI     | Do not display the UI                                                                  |

"Headless" mode, with _--no-gui_ specified, requires that, as a minimum, a simulation file is provided.

## Setting and Saving Options

From the _Simulation_ menu, select _Options_ to show a tabbed
options dialog as follows:

![Options Dialog](https://github.com/davewalker5/OdeSolver/blob/main/docs/images/options_function_tab.png?raw=true)

The following table summarises the available options:

| Tab                   | Option            | Comments                                                        |
| --------------------- | ----------------- | --------------------------------------------------------------- |
| Chart Properties      | Title             | Chart title (optional)                                          |
|                       | Y(min)            | Optional if automatic scaling is enabled                        |
|                       | Y(max)            | Optional if automatic scaling is enabled                        |
|                       | X(max)            | Optional if automatic scaling is enabled                        |
|                       | Automatic scaling | If ticked, chart axes are automatically scaled to the data      |
| Function definition   | Function          | Definition of the ODE to solve and hooks, in Python (see below) |
| Simulation Parameters | Method            | Integration method to use                                       |
|                       | Limit of x        | End the simulation when x reaches thislimit or;                 |
|                       | No. steps         | End the simulation after this number of steps                   |
|                       | Initial step size | Initial step size                                               |
|                       | Initial y         | Initial value of y                                              |
| Step Adjustment       | Tolerance         | Tolerance to be used when automatic step size is enabled        |
|                       | Adjust step size  | If ticked, automatically adjust step size                       |

Once set, options can be saved to a JSON format file using the _Save_ option on the _File_ menu. Saved settings can be loaded from the _Load_ option, also on the _File_ menu.

## Function Definitions

The ODE Solver provides hooks for 2 functions:

| Function Name | Mandatory | Signature                               | Return  | Description                            |
| ------------- | --------- | --------------------------------------- | ------- | -------------------------------------- |
| f             | Yes       | f(t: Decimal, y: Decimal) -> Decimal    | Decimal | The differential equation to be solved |
| pre_hook      | No        | pre_hook()  -> None                     | None    | Implement pre-simulation actions       |
| post_hook     | No        | post_hook(history: list[dict])  -> None | None    | Implement post-simulation actions      |

All three are set in a single Python script on the _Function_ tab of the options dialog, as illustrated above.

_f_, the equation being solved, must return a single Decimal value that is the value of the function calculated from the input parameters.

Additional supporting methods and constants may be defined in the function definition, if needed.

The following is an example in which the pre-simulation hook just prints a message and the post-simulation hook just pretty-prints the run-history:

```python
from decimal import Decimal
from pprint import pprint as pp

A = Decimal("0.5")

def pre_hook() -> None:
  print("Pre-simulation hook called")

def post_hook(history: list[dict]) -> None:
  pp(history)

def f(_, y: Decimal) -> Decimal:
  """
  dy/dx = Ay

  :param _: Independent variable (not used in this example)
  :param y: Dependent variable
  :return: Next value of the dependent variable
  """
  return A * y
```

## Running the Solution

To solve the current ODE using the current options, select the _Run_ option from the _Simulation_ menu. If the options are all valid, and all mandatory options have been specified, the solution is run and both the chart (see above) and the data table will be updated as each point is added to the solution.

An example of the data table is shown below:

![Data Table](https://github.com/davewalker5/OdeSolver/blob/main/docs/images/data_table_tab.png?raw=true)

If the options are invalid or incomplete when the solution is run, a warning message will be displayed, indicating which options have not been specified, and the solution will not run.

## Exporting Results

Once the solution has been run, the data can be exported from the _Export_ option on the _File_ menu. Supported formats are CSV, JSON and XML. If an export option is selected without having run the solution, a warning dialog is displayed.

# Unit Tests and Coverage

To run the unit tests, a virtual environment should be created, the requirements should be installed using pip and the environment should be activated.

The tests can then be run from the command line, at the root of the project folder, as follows:

```bash
export PYTHONPATH=`pwd`/src/
python -m pytest
```

The first command adds the source folder, containing the packages under test, to the PYTHONPATH environment variable so the packages will be found when the tests attempt to import them. The command will need to be modified based on the current operating system.

Similarly, a coverage report can be generated by running the following commands from the root of the project folder:

```bash
export PYTHONPATH=`pwd`/src/
python -m pytest --cov=src --cov-branch --cov-report html
```

This will create a folder _htmlcov_ containing the coverage report in HTML format.

# Generating Documentation

To generate the documentation, a virtual environment should be created,
the requirements should be installed using pip and the environment
should be activated.

HTML documentation can then be created by running the following commands
from the _docs_ sub-folder:

```bash
export PYTHONPATH=`pwd`/../src/
make html
```

The resulting documentation is written to the docs/build/html folder and can be viewed by opening _index.html_ in a web browser.

# License

This software is licensed under the MIT License:

<https://opensource.org/licenses/MIT>

Copyright 2022 - 2026 David Walker

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the _Software_), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED _AS IS_, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
