# Winter Visitor ODE Model

This module defines a simple first-order ordinary differential equation (ODE) intended to model the observable activity or detectability of a wildlife species over time, driven by seasonal forcing.

It's applicable to winter visitors that exhibit a single annual peak in presence that wraps around the end of the year. Examples are:

- Redwing (Turdus iliacus)

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
| T(t) | Seasonal target | A periodic function representing expected seasonal activity for a winter visitor         |
| rate | Response rate   | Controls how quickly y responds to changes in the seasonal target                        |

The seasonal target T(t) is constructed as a combination of:

- A **winter component**, representing peak presence during the core winter months
- An optional **autumn component**, representing arrival into the winter season
- A **summer suppression component**, reducing activity during the off-season

Each component is defined as a smooth periodic function over a 12-month cycle. Time is treated as circular, allowing the model to represent seasons that wrap across the end of the year (e.g. October–March).

## Units

All seasonal components are dimensionless shape functions.

y(t) is a relative or scaled measure of activity, representing observable presence or detectability.

Time is measured in months and treated as a circular quantity over a 12-month cycle.

GROWTH_RATE and DECAY_RATE are time-scale parameters (units of 1/time) controlling how quickly the system responds to changes in the seasonal target.

## Key features

1. Circular time handling:<br/>
   Time is wrapped onto a 12-month cycle using modulo arithmetic, allowing seasons to cross the calendar boundary.

2. Composite seasonal structure:<br/>
   The seasonal target combines winter, autumn, and summer components, allowing flexible modelling of arrival, peak presence, and absence.

3. Smooth periodic forcing:<br/>
   Raised-cosine style functions are used to produce continuous, differentiable seasonal curves without discontinuities.

4. Asymmetric dynamics:<br/>
   Separate growth and decay rates allow the model to represent faster decline after the winter peak.

5. Explicit modelling of arrival phase:<br/>
   A distinct autumn component allows the timing and shape of arrival into the winter season to be modelled independently.

6. Active summer suppression:<br/>
   A summer component reduces activity during the off-season, producing near-zero values where the species is absent.

## Numerical considerations

- All calculations are performed using Decimal for deterministic and high-precision arithmetic.
- Custom implementations of sin() and cos() are used to avoid mixing float and Decimal arithmetic.
- The sine function is computed via a Taylor series expansion, with convergence controlled by a fixed tolerance.

## Interpretation

This is a deliberately simplified "toy" model intended to explore whether simple mechanistic assumptions can reproduce observed seasonal patterns in wildlife records.

The model is particularly suited to species whose main period of presence crosses the calendar boundary (e.g. winter visitors such as Redwing and Fieldfare).

The fitted parameters are now broadly interpretable in ecological terms, especially when derived from multiple fitting runs and summarised (e.g. using median values).

Key parameters can be interpreted as follows:

- WINTER_PEAK → approximate timing of peak winter presence
- AUTUMN_PEAK → approximate timing of arrival into the winter season
- WINTER_WIDTH → concentration of winter presence around the peak (higher values = narrower peak)
- AUTUMN_WIDTH → spread of the autumn arrival phase
- WINTER_WEIGHT → relative strength of winter presence
- AUTUMN_WEIGHT → relative strength of the autumn arrival signal
- SUMMER_DIP / SUMMER_LOW → timing and strength of summer absence

These parameters provide a compact and comparable description of seasonal behaviour across species.

However, the model output arises from the interaction of multiple components, and parameters should be interpreted as estimates rather than exact measurements. Interpretation is most robust when:

- considering multiple fitting runs
- summarising parameter values (e.g. median and spread)
- validating against the fitted curve

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

The fitted parameters are now broadly interpretable in ecological terms, particularly when derived from multiple fitting runs and summarised.

Because the parameter search is constrained using the observed data, key parameters tend to align with real seasonal features:

- WINTER_PEAK → timing of peak winter presence
- AUTUMN_PEAK → timing of arrival into the winter season
- WINTER_WIDTH → concentration of activity around the winter peak
- AUTUMN_WIDTH → breadth of the arrival phase

These parameters allow species to be compared in terms of:

- Timing of peak presence
- Timing of arrival
- Sharpness or breadth of the winter season

However:

- Parameters should be interpreted as estimates, not exact dates
- Different parameter combinations may produce similar curves
- Individual runs may vary due to stochastic sampling

As with the seasonal model, interpretation is most reliable when combining:

- The fitted parameters
- The shape of the simulated curve

### Scoring

Model fit is evaluated using a combination of:

- Mean Squared Error (MSE) — overall curve similarity
- Additional penalties for:
  - Peak timing mismatch (using circular month distance)
  - Incorrect seasonal positioning
  - Simulated presence in months where observed values are near zero

The use of circular month distance ensures that comparisons across the year boundary (e.g. December–January) are handled correctly.

Penalising presence in inactive months helps prevent overly broad seasonal curves, ensuring that winter activity is both well-timed and appropriately constrained.

This scoring approach favours solutions that are both mathematically close to the observed data and ecologically realistic.

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

#### 4. Generate the Synthesised Chart

Once the solver has completed, generate the synthesised data:

```bash
./scripts/synthesise.sh <species>
```

This generates synthesised data, scaled per the observed data but following the curve of the simulated output, and writes the <em>species_synthesised.csv</em> and <em>species_synthesised.png</em> files to the _data_ folder. The chart is particularly useful as a visual comparison of how well the model and parameter fitting has worked for the species in question.