# Seasonal Presence ODE Model

This module defines a simple first-order ordinary differential equation (ODE) intended to model the observable activity or detectability of a wildlife species over time, driven by seasonal forcing.

## Model overview

A single state variable y(t) is modelled as:

```
y(t) = observable activity / detection rate
```

The governing equation is:

```
dy/dt = GROWTH * S(t) * W(t) - decay(t) * y
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

| File                            | Species                              | Comments                                                                          |
| ------------------------------- | ------------------------------------ | --------------------------------------------------------------------------------- |
| seasonal_params.json            | -                                    | Example species parameters file for the seasonal_presence_generic.json simulation |
| seasonal_presence_bluebell.json | Bluebell (Hyacinthoides non-scripta) | Simulation for the bluebell, species parameters embedded                          |
| seasonal_presence_generic.json  | -                                    | Simulation that loads species from the external parameters JSON file              |
| seasonal_presence_swift.json    | Swift (Apus apus)                    | Simulation for the swift, species parameters embedded                             |

The "generic" model loads species parameters from a separate JSON file pointed at run-time. That file has the following format:

```json
{
  "GROWTH": "2.0",
  "DECAY": "1.5",
  "OOS_DECAY": "3.0",
  "SEASON_START": "5.11",
  "SEASON_END": "9.61",
  "SHARPNESS": "3.421",
  "FORCING_PEAK": "3.65"
}
```

The environment variable SEASONAL_PARAMS_FILE must be set to point to this file before running the simulation.

## Parameter Fitting

Given observed data (typically monthly presence or detectability), the parameter fitting script:

1. Generates a candidate set of model parameters
2. Runs the ODE Solver in headless mode
3. Compares the simulated curve to observed data
4. Scores the match
5. Repeats to find the best fit

This produces a set of parameters that describe the species’ seasonal behaviour.

### What the parameters mean

Fitted parameters are not arbitrary — they are interpretable, for example:

- SEASON_START &rarr; when the species begins to appear
- SEASON_END &rarr; when it disappears
- FORCING_PEAK &rarr; peak timing
- SHARPNESS &rarr; how abrupt the seasonal transitions are

These provide a compact way to compare species and patterns.

### Scoring

Model fit is evaluated using:

- Mean Squared Error (MSE) — overall curve similarity
- Additional penalties for:
  - Peak timing mismatch
  - Incorrect season start
  - Incorrect season end

This ensures the model captures both:

- The shape of the curve
- The timing of the season

### Running the Parameter Fitter

Before attempting to run the parameter fitter, the following environment variable must be set:

```
export RUN_ODE_SOLVER=/path/to/ODE/solver/run-solver.sh
```

A CSV file containing the observed data for the species of interest should be prepared. For example:

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

The parameter fit can then be run as follows

```bash
run-fit.sh /path/to/observed/data.csv
```

The script will report the latest "best" match as it progresses and on completion will report the parameters yielding the best fit:

```
Best fit
--------
Score: 0.02419324807468518344653567672
{
  "GROWTH": "2.0",
  "DECAY": "1.5",
  "OOS_DECAY": "3.0",
  "SEASON_START": "3.97",
  "SEASON_END": "7.26",
  "SHARPNESS": "1.509",
  "FORCING_PEAK": "8.42"
}
```

Those parameters are also written to the file _best_params.json_.