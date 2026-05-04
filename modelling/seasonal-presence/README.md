# Seasonal Presence ODE Model

This module defines a simple first-order ordinary differential equation (ODE) intended to model the observable activity or detectability of a wildlife species over time, driven by seasonal forcing.

It's applicable to species that exhibit a single annual peak in presence that doesn't wrap around the end of the year. Examples are:

- Migratory birds
- Flowers with a single flowering period
- Butterflies with a single flight period

## Model overview

A single state variable y(t) is modelled as:

```
y(t) = observable activity / detection rate
```

The governing equation is:

```
dy/dt = GROWTH - S(t) - W(t) - decay(t) * y
```

Where:

| Term     | Name                                     | Meaning                                                                                                                                                                   |
| -------- | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| S(t)     | Seasonal forcing (sinusoidal)            | Represents underlying environmental drivers such as day length, temperature, or resource availability                                                                     |
| W(t)     | Seasonal window (logistic rise and fall) | Constrains activity to a biologically plausible time window (e.g. breeding season, flowering period, migration presence)                                                  |
| decay(t) | State-dependent damping                  | Controls how quickly activity declines. Increased outside the seasonal window to simulate rapid shutdown (e.g. senescence,dispersal, mortality, or behavioural switching) |

## Units

S(t) and W(t) are dimensionless shape functions.

y(t) is a relative or scaled measure of activity, a dimensionless
activity index proportional to observable presence or detectability.

Both GROWTH and the return from the decay() function are time-scale
parameters, or rates, measured in units of 1/time, and control the
characteristic timescale of rise and decay in the system.


## Key features

1. Periodic forcing:<br/>
   Time is wrapped onto a 12-month cycle using modulo arithmetic.

2. Raised-cosine seasonal forcing:<br/>
   The seasonal forcing is scaled onto the range 0..1, giving a smooth annual curve without a hard zero at the start of the year.

3. Smooth seasonal window:<br/>
   Logistic functions are used for both onset and decline of the active period, avoiding discontinuities.

4. Enhanced out-of-season decay:<br/>
   Activity is actively suppressed outside the window, not just passively decaying.


## Numerical considerations

- All calculations are performed using Decimal for deterministic and high-precision arithmetic.
- Custom implementations of exp() and sin() are used to avoid mixing float and Decimal arithmetic.
- The sine function is computed via a Taylor series expansion, with convergence controlled by a fixed tolerance.


## Interpretation

This is a deliberately simplified "toy" model intended to explore whether simple mechanistic assumptions can reproduce observed seasonal patterns in wildlife records.

Parameters such as GROWTH, DECAY, SEASON_START, and SEASON_END can be tuned to represent different ecological strategies:

- Narrow window, high decay -> short-lived or highly seasonal species
- Broad window, low decay -> resident or persistent species
- High growth -> strong seasonal signal

The model is not intended for precise prediction, but for pattern exploration and comparison with empirical data.

## Simulation Files

The following ODE Solver simulation files are provided in the "simulations" folder:

| File                           | Species | Comments                                                             |
| ------------------------------ | ------- | -------------------------------------------------------------------- |
| seasonal_presence_generic.json | -       | Simulation that loads species from the external parameters JSON file |

The "generic" model loads species parameters from a separate JSON file pointed at run-time. That file has the following format:

```json
{
  "GROWTH": "2",
  "DECAY": "1.5",
  "OOS_DECAY": "3",
  "SEASON_START": "4.905",
  "SEASON_END": "8.73",
  "SHARPNESS": "6.175",
  "FORCING_PEAK": "5.21"
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

The fitted parameters are now broadly interpretable in ecological terms, but should still be treated with appropriate caution.

Because the parameter search is constrained using the observed data, key parameters tend to align with real seasonal features:

- SEASON_START &rarr; approximate onset of seasonal presence
- SEASON_END &rarr; approximate end of the season
- FORCING_PEAK &rarr; approximate timing of peak activity
- SHARPNESS &rarr; how abruptly the season begins and ends

These parameters provide a compact and comparable description of seasonal behaviour across species.

However, the model output still arises from the interaction of multiple components (seasonal window, forcing function, growth/decay dynamics). As a result:

- Parameters should be interpreted as estimates, not exact dates
- Different parameter combinations may still produce similar curves
- Individual runs may vary slightly due to stochastic sampling

For this reason, interpretation is most reliable when:

- Considering multiple runs rather than a single fit
- Summarising parameters (e.g. median and spread)
- Validating against the fitted curve itself

In practice, the most robust ecological interpretation combines both:

- The fitted parameters
- The shape and timing of the simulated curve

### Scoring

Model fit is evaluated using a combination of:

- Mean Squared Error (MSE) — overall curve similarity
- Additional penalties for:
    - Peak timing mismatch
    - Incorrect season start
    - Incorrect season end

This ensures the model captures both:

- The shape of the curve
- The timing of the season

By combining these components, the fitting process favours solutions that are not only mathematically close to the observed data, but also ecologically realistic.

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
1,0
2,0
3,0
4,1
5,33
6,54
7,40
8,7
9,4
10,0
11,0
12,0
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