# Resident Detectability ODE Model

This module defines a simple first-order ordinary differential equation (ODE) intended to model the observable activity or detectability of a resident wildlife species over time.

Unlike the seasonal model, which represents species that appear and disappear during the year, this model assumes continuous presence, with only detectability varying seasonally.

## Model overview

A single state variable y(t) is modelled as:

```
y(t) = observable activity / detection rate
```

The governing equation is:

```
dy/dt = RESPONSE_RATE - (target(t) - y)
```

Where:

| Term          | Name                          | Meaning                                                                    |
| ------------- | ----------------------------- | -------------------------------------------------------------------------- |
| target(t)     | Seasonal detectability target | Expected detectability at time t, based on seasonal behaviour              |
| RESPONSE_RATE | Relaxation rate               | Controls how quickly the system responds to changes in the seasonal target |

## Units

- y(t) is a dimensionless activity index, representing relative detectability
- target(t) is also dimensionless, defined on an arbitrary but consistent scale
- RESPONSE_RATE has units of 1/time (e.g. per month), and controls the timescale over which the system responds

## Key features

1. Continuous presence:<br/>
    The model assumes the species is present year-round, with no enforced absence.
2. Target-driven dynamics:<br/>
    Detectability is not generated or destroyed directly, but instead relaxes towards a seasonal target.
3. Smooth periodic forcing:<br/>
    The target function is constructed from smooth annual components (raised-cosine “bumps”), producing a continuous yearly cycle.
4. Multi-component seasonality:<br/>
    The target combines:<br/>
    - A persistent baseline
    - A winter / early-spring peak
    - An autumn / early-winter recovery
    - A summer dip
5. Asymmetric response (optional):<br/>
    Different rates can be applied for increases vs decreases in detectability, allowing faster declines and slower recovery.

## Numerical considerations

- All calculations are performed using Decimal for deterministic and high-precision arithmetic
- Custom implementations of trigonometric functions are used to avoid mixing float and Decimal arithmetic
- The model is stable and well-behaved over long integrations, but initial conditions influence early behaviour

## Interpretation

This model is intended to represent species that are always present but variably detectable, such as robin, blackbird, or wren.

It answers a different ecological question to the seasonal model:

- Seasonal model &rarr; “When is the species present?”
- Resident model &rarr; “How detectable is the species through the year?”

The structure reflects this distinction:

- No seasonal window or shutdown
- No growth-from-zero behaviour
- Continuous tracking of a seasonal signal

## Parameter interpretation

Key parameters control different aspects of behaviour:

| Parameter                                | Purpose                                                                     |
| ---------------------------------------- | --------------------------------------------------------------------------- |
| BASELINE                                 | Minimum year-round detectability                                            |
| WINTER_WEIGHT, AUTUMN_WEIGHT, SUMMER_DIP | Relative strength of seasonal components                                    |
| *_PEAK                                   | Timing of seasonal features                                                 |
| *_WIDTH                                  | Breadth or sharpness of peaks/dips                                          |
| RESPONSE_RATE                            | How quickly detectability adjusts to seasonal changes                       |
| GROWTH_RATE / DECAY_RATE (if used)       | Allow asymmetric dynamics (e.g. faster summer decline than winter recovery) |

## Comparison with Seasonal Model

| Feature          | Seasonal Model             | Resident Model            |
| ---------------- | -------------------------- | ------------------------- |
| Presence         | Can be zero outside season | Always non-zero           |
| Dynamics         | Growth and decay           | Relaxation towards target |
| Seasonal control | Window + forcing           | Target function           |
| Typical species  | Swift, bluebell            | Robin, blackbird          |

## Usage notes

- Initial conditions matter: for resident species, starting y near the baseline or observed value improves realism
- Running the model for multiple years and plotting the final year removes transient effects
- The model is best used for pattern exploration, not precise prediction
