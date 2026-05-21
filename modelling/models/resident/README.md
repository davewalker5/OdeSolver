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
dy/dt = rate - (T(t) - y)
```

Where:

| Term | Name            | Meaning                                                                                 |
| ---- | --------------- | --------------------------------------------------------------------------------------- |
| T(t) | Seasonal target | A periodic function representing expected seasonal detectability for a resident species |
| rate | Response rate   | Controls how quickly y responds to changes in the seasonal target                       |

The seasonal target T(t) is constructed as a combination of:

- A baseline level, representing year-round presence
- A winter component, representing increased detectability during winter
- An optional autumn component, representing late-year behavioural changes
- A summer suppression component, representing reduced detectability during quieter summer periods
- An optional spring carry-over component, allowing detectability to remain elevated through spring and early summer before entering the summer low

The model also supports:

- Delayed onset of rapid summer decline
- Reduced pre-summer decay
- Asymmetric recovery behaviour

These mechanisms allow the model to represent species whose detectability declines gradually through spring before entering a sharper summer reduction phase.

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

## Extended seasonal dynamics

Some resident species exhibit a prolonged spring decline followed by a relatively abrupt late-summer reduction in detectability.

To support this behaviour, the model includes additional optional mechanisms:

| Mechanism                  | Purpose                                                               |
| -------------------------- | --------------------------------------------------------------------- |
| Pre-summer decay reduction | Slows the decline in detectability during spring and early summer     |
| Delayed summer decay onset | Prevents rapid summer collapse from beginning too early               |
| Summer decay boost         | Allows sharper summer suppression once the summer low begins          |
| Spring carry-over          | Maintains elevated detectability through spring before summer decline |

These mechanisms are particularly useful for species such as:

- Common Blackbird
- European Robin

while still allowing simpler resident patterns for species such as:

- Eurasian Blue Tit

The parameter fitting system constrains these behaviours automatically based on the observed seasonal signal.

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

### Additional Resident Dynamics Parameters

Some fitted parameters describe the persistence and timing of seasonal decline rather than the timing of seasonal peaks.

Examples include:

- PRE_SUMMER_DECAY_REDUCTION &rarr; strength of retained spring detectability
- SUMMER_DECAY_ONSET &rarr; timing of rapid summer decline
- SUMMER_DECAY_BOOST &rarr; intensity of summer suppression
- SPRING_CARRYOVER_WEIGHT &rarr; persistence of elevated detectability through spring

These parameters are especially important for species with broad seasonal plateaus or delayed summer decline.

## Simulation Files

The following ODE Solver simulation files are provided in the "simulations" folder:

| File                                | Species | Comments                                                             |
| ----------------------------------- | ------- | -------------------------------------------------------------------- |
| resident_detectability_generic.json | -       | Simulation that loads species from the external parameters JSON file |

The "generic" model loads species parameters from a separate JSON file pointed at run-time. That file has the following format:

```json
{
  "SCORE": "0.255",
  "INITIAL_Y": "0.915",
  "GROWTH_RATE": "1.666",
  "DECAY_RATE": "3.141",
  "SUMMER_DECAY_BOOST": "3.932",
  "PRE_SUMMER_DECAY_REDUCTION": "0.49",
  "PRE_SUMMER_DECAY_END": "7.05",
  "PRE_SUMMER_DECAY_SHARPNESS": "9.225",
  "SPRING_CARRYOVER_WEIGHT": "0.051",
  "SPRING_CARRYOVER_END": "7.04",
  "SPRING_CARRYOVER_SHARPNESS": "15.53",
  "BASELINE": "0.327",
  "WINTER_WEIGHT": "0.426",
  "AUTUMN_WEIGHT": "0.02",
  "WINTER_PEAK": "3.06",
  "AUTUMN_PEAK": "10.9",
  "AUTUMN_ONSET": "9.815",
  "AUTUMN_GATE_SHARPNESS": "7.692",
  "WINTER_WIDTH": "9.748",
  "WINTER_RISE_WIDTH": "10.241",
  "WINTER_FALL_WIDTH": "10.266",
  "AUTUMN_WIDTH": "7.559",
  "AUTUMN_RISE_WIDTH": "6.348",
  "AUTUMN_FALL_WIDTH": "8.598",
  "SUMMER_DIP": "0.156",
  "SUMMER_LOW": "7.595",
  "SUMMER_ONSET": "5.455",
  "SUMMER_GATE_SHARPNESS": "4.603",
  "SUMMER_DECAY_ONSET": "7.13",
  "SUMMER_DECAY_GATE_SHARPNESS": "14.938",
  "SUMMER_WIDTH": "21.02",
  "SUMMER_RISE_WIDTH": "33.129",
  "SUMMER_FALL_WIDTH": "9.624",
  "SCALE": "1.298",
  "YEAR_END_WEIGHT": "0.156",
  "YEAR_END_PEAK": "12.132",
  "YEAR_END_WIDTH": "90.288",
  "YEAR_END_RISE_WIDTH": "172.07",
  "YEAR_END_FALL_WIDTH": "10.192",
  "SPECIES": "Blue Tit"
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

The following summarises the naming conventions and locations for the outputs from the modelling process:

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

#### 4. Generate the Synthesised Chart

Once the solver has completed, generate the synthesised data:

```bash
./scripts/synthesise.sh <species>
```

This generates synthesised data, scaled per the observed data but following the curve of the simulated output, and writes the <em>species_synthesised.csv</em> and <em>species_synthesised.png</em> files to the _data_ folder. The chart is particularly useful as a visual comparison of how well the model and parameter fitting has worked for the species in question.
