# Winter Visitor ODE Model

This module defines a simple first-order ordinary differential equation (ODE) intended to model the observable activity or detectability of a wildlife species over time, driven by seasonal forcing.

It's applicable to winter visitors that exhibit a single annual peak in presence that wraps around the end of the year. Examples are:

- Redwing

## Model overview

TBC

## Units

TBC

## Key features

TBC

## Numerical considerations

- All calculations are performed using Decimal for deterministic and high-precision arithmetic.
- Custom implementations of sin() and cos() are used to avoid mixing float and Decimal arithmetic.
- The sine function is computed via a Taylor series expansion, with convergence controlled by a fixed tolerance.

## Interpretation

This is a deliberately simplified "toy" model intended to explore whether simple mechanistic assumptions can reproduce observed seasonal patterns in wildlife records.

TBC

The model is not intended for precise prediction, but for pattern exploration and comparison with empirical data.

## Simulation Files

The following ODE Solver simulation files are provided in the "simulations" folder:

| File                        | Species | Comments                                                             |
| --------------------------- | ------- | -------------------------------------------------------------------- |
| winter_visitor_generic.json | -       | Simulation that loads species from the external parameters JSON file |

The "generic" model loads species parameters from a separate JSON file pointed at run-time. That file has the following format:

```json
{
  "INITIAL_Y": "1.013",
  "GROWTH_RATE": "0.65",
  "DECAY_RATE": "2.834",
  "BASELINE": "0",
  "WINTER_WEIGHT": "1.174",
  "AUTUMN_WEIGHT": "0.098",
  "WINTER_PEAK": "1.84",
  "AUTUMN_PEAK": "11.485",
  "WINTER_WIDTH": "3.748",
  "AUTUMN_WIDTH": "3.544",
  "SUMMER_DIP": "0.308",
  "SUMMER_LOW": "6.825",
  "SUMMER_WIDTH": "3.145"
}
```

The environment variable SEASONAL_PARAMS_FILE must be set to point to this file before running the simulation.

## Parameter Fitting

Given observed data (typically monthly presence or detectability), the parameter fitting script:

1. Analyses the observed data to infer a plausible seasonal window
2. Generates candidate sets of model parameters within that constrained space
3. Runs the ODE Solver in headless mode
4. Compares the simulated curve to observed data
5. Scores the match
6. Repeats to identify the best-fitting parameter sets

This produces a set of parameters that describe the species’ seasonal behaviour.

To improve robustness, multiple fitting runs can be performed. The best-performing runs can then be summarised (e.g. using median values) to produce a stable parameter estimate.

## Interpreting the fitted parameters

TBC

### Scoring

TBC

### Running the Parameter Fitter

#### Overview

The parameter fitting workflow is illustrated below:

![Parameter Fitting](https://github.com/davewalker5/OdeSolver/blob/main/docs/images/parameter-fitting.png?raw=true)

The following summarises

| File              | Naming                          | Type      | Location    |
| ----------------- | ------------------------------- | --------- | ----------- |
| observed.csv      | <em>species</em>_observed.csv   | Input     | data folder |
| parameters.csv    | <em>species</em>_parameters.csv | Generated | data folder |
| consensus.json    | <em>species</em>consensus.json  | Generated | data folder |
| simulated results | <em>species</em>simulated.csv   | Generated | data folder |
| simulated results | <em>species</em>simulated.png   | Generated | data folder |

Where _species_ is the name of the species of interest e.g. swift, swallow etc.

Files marked as "generated" are created by the parameter fitting and related scripts. The input file should be prepared beforehand and should contain a month column, with values 1 to 12, and a value column indicating the observed value in that month:

```csv
month,value
1,24
2,26
3,14
4,1
5,0
6,0
7,0
8,0
9,0
10,0
11,0
12,6
```

The value may be total counts or "presence" values (for more information on presence, see _Seasonal Analyses_ in the _Wildlife_ section of the [Field Notes &nearr;](https://davidwalker.uk/) site).

#### 1. Parameter Fitting

The parameter fitting step is run using:

```bash
./scripts/run-fit.sh <species>
```

This outputs the <em>species_parameters.csv</em> file and the best-fit parameters to <em>data/species_best.json</em>, both in the _data_ folder.

#### 2. Consensus Parameter Generation

Once the fit has been completed, the consensus parameter calculation can be run using:

```bash
./scripts/run-consensus.sh <species>
```

This outputs the _species_consensus.json_ file in the _data_ folder.

#### 3. Running the Solution

Once the consensus parameters have been generated, the solution can be run with those parameters using:

```bash
./scripts/run-solver.sh <species>
```

This runs the ODE Solver UI to view the simulation and writes the <em>species_simulated.csv</em> and <em>species_simulated.png</em> files to the _data_ folder.