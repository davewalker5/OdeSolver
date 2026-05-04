# Resident Detectability ODE Model

This module defines a simple first-order ordinary differential equation (ODE) intended to model the observable activity or detectability of a resident wildlife species over time, representing species that are always present but variably detectable. Examples are:

- Robin (Erithacus rubecula)
- Blackbird (Turdus merula)
- Wren (Troglodytes troglodytes)

## Model overview

A single state variable y(t) is modelled as:

```
y(t) = observable activity / detection rate
```

The governing equation is:

```
dy/dt = rate * (T(t) - y)
```

Where:

| Term | Name            | Meaning                                                                                  |
|------|-----------------|------------------------------------------------------------------------------------------|
| T(t) | Seasonal target | A periodic function representing expected seasonal detectability for a resident species |
| rate | Response rate   | Controls how quickly y responds to changes in the seasonal target                        |

The seasonal target T(t) is constructed as a combination of:

- A **baseline level**, representing year-round presence
- A **winter component**, representing increased detectability during winter
- An optional **autumn component**, representing late-year behavioural changes
- A **summer suppression component**, representing reduced detectability in summer

Each component is defined as a smooth periodic function over a 12-month cycle. Time is treated as circular, allowing the model to represent continuous seasonal variation without a true "on/off" season.

## Units

All seasonal components are dimensionless shape functions.

y(t) is a relative or scaled measure of activity, representing observable presence or detectability.

Time is measured in months and treated as a circular quantity over a 12-month cycle.

GROWTH_RATE and DECAY_RATE are time-scale parameters (units of 1/time) controlling how quickly the system responds to changes in the seasonal target.

## Key features

1. Continuous presence:<br/>
   The model assumes the species is present year-round, with no seasonal shutdown.

2. Circular time handling:<br/>
   Time is wrapped onto a 12-month cycle using modulo arithmetic.

3. Composite seasonal structure:<br/>
   Detectability is modelled as the combination of baseline, winter, autumn, and summer components.

4. Smooth periodic forcing:<br/>
   Raised-cosine style functions produce continuous, differentiable seasonal curves without discontinuities.

5. Explicit summer low:<br/>
   A summer component allows modelling of reduced detectability during quieter periods.

6. Asymmetric dynamics:<br/>
   Separate growth and decay rates allow the model to represent differing rates of increase and decline in detectability.

## Numerical considerations

- All calculations are performed using Decimal for deterministic and high-precision arithmetic
- Custom implementations of trigonometric functions are used to avoid mixing float and Decimal arithmetic
- The model is stable and well-behaved over long integrations, but initial conditions influence early behaviour

## Interpretation

This model is intended to represent species that are always present but variably detectable.

It answers a different ecological question to the seasonal and winter visitor models:

- Seasonal model &rarr; “When is the species present?”
- Winter visitor model &rarr; “When is the species present?”
- Resident model &rarr; “How detectable is the species through the year?”

The structure reflects this distinction:

- No seasonal window or shutdown
- No growth-from-zero behaviour
- Continuous tracking of a seasonal signal

## Simulation Files

The following ODE Solver simulation files are provided in the "simulations" folder:

| File                        | Species | Comments                                                             |
| --------------------------- | ------- | -------------------------------------------------------------------- |
| resident_detectability_generic.json | -       | Simulation that loads species from the external parameters JSON file |

The "generic" model loads species parameters from a separate JSON file pointed at run-time. That file has the following format:

```json
{
  "INITIAL_Y": "1.525",
  "GROWTH_RATE": "1.294",
  "DECAY_RATE": "0.648",
  "BASELINE": "0.51",
  "WINTER_WEIGHT": "1.035",
  "AUTUMN_WEIGHT": "0.171",
  "WINTER_PEAK": "1.73",
  "AUTUMN_PEAK": "10.77",
  "WINTER_WIDTH": "2.754",
  "AUTUMN_WIDTH": "2.365",
  "SUMMER_DIP": "0.613",
  "SUMMER_LOW": "6.0",
  "SUMMER_WIDTH": "1.292",
  "TIMESTAMP": "2026-05-04 11:20:33",
  "OBSERVED": "robin_observed.csv",
  "SCORE": "0.04686333499774545355656549744"
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

The fitted parameters are broadly interpretable in ecological terms, particularly when derived from multiple fitting runs and summarised.

Because the parameter search is constrained using the observed data, key parameters tend to align with real seasonal features:

- WINTER_PEAK &rarr; timing of highest detectability (typically mid-winter)
- AUTUMN_PEAK &rarr; timing of late-year increase in detectability
- SUMMER_LOW &rarr; timing of lowest detectability
- WINTER_WIDTH &rarr; concentration of winter detectability around the peak
- AUTUMN_WIDTH &rarr; breadth of the autumn increase
- SUMMER_WIDTH &rarr; breadth of the summer low

These parameters describe how detectability varies through the year rather than when the species is present.

However:

- Parameters should be interpreted as estimates, not exact dates
- Different parameter combinations may produce similar curves
- Individual runs may vary due to stochastic sampling

Interpretation is most reliable when combining:

- The fitted parameters
- The shape of the simulated curve

### Scoring

Model fit is evaluated using a combination of:

- Mean Squared Error (MSE) — overall curve similarity
- Additional penalties for:
  - Peak timing mismatch (using circular month distance)
  - Incorrect timing of seasonal high and low points

Unlike the seasonal and winter visitor models, no penalty is applied for simulated presence in low-value months, as the species is assumed to be present year-round.

The use of circular month distance ensures that comparisons across the year boundary (e.g. December–January) are handled correctly.

This scoring approach favours solutions that capture both the shape of the detectability curve and the timing of seasonal variation.


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
1,138
2,107
3,110
4,103
5,96
6,55
7,31
8,35
9,58
10,59
11,50
12,85
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
