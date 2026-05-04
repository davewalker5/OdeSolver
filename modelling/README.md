# Wildlife Seasonal Pattern Modelling

This folder contains a set of simple mathematical models and supporting tools used to explore seasonal patterns in wildlife observations.

The aim is not to produce perfect predictions, but to build interpretable models that help answer a straightforward question:

> What underlying seasonal behaviour best explains the patterns we observe in the field?

## Overview

Field observations (e.g. bird sightings, plant records) often show strong seasonal structure:

- Species appear and disappear at particular times of year
- Detectability varies through the seasons
- Peaks of activity or abundance occur at characteristic times

These patterns can be described using simple models, and — importantly — fitted back to real data to extract meaningful parameters.

This folder contains:

- Models of seasonal behaviour
- Simulation configurations for the ODE Solver
- A parameter fitting system that matches models to observed data

## Key Ideas

### 1. Observations are noisy

Raw field data reflects:

- True biological behaviour
- Observer availability
- Weather and conditions
- Chance

The goal of modelling here is to recover the underlying seasonal signal.

### 2. Models are deliberately simple

The models in this folder are based on:

- Smooth seasonal forcing (annual cycles)
- Simple growth and decay dynamics
- Soft “season windows” (start and end of activity)

They are designed to be:

- Interpretable
- Stable
- Easy to compare across species

The emphasis is on:

- Clarity over complexity
- Interpretability over optimisation
- Usefulness for natural history observation

### 3. Parameter fitting

Parameter fitting is currently implemented for the model for seasonally present and winter visitor models, rather than residents where observations are driven by detectability changes.

Given observed data (typically monthly presence or detectability), we:

1. Generate a candidate set of model parameters
2. Run the ODE Solver in headless mode
3. Compare the simulated curve to observed data
4. Score the match
5. Repeat to find the best fit

This produces a set of parameters that describe the species’ seasonal behaviour.

## Folder Structure

### seasonal-presence/

Models species that are absent outside a defined season, where that season doesn't wrap the boundaries of the year, such as:

- Swifts (Apus apus)
- Swallows (Hirundo rustica)
- Flowering plants such as the bluebell (Hyacinthoides non-scripta)

### winter-visitor/

Models species that are absent outside the autumn/winter season, such as:

- Redwing (Turdus iliacus)
- Fieldfare (Turdus pilaris)

### resident-detectability/

Models species that are present year-round, but vary in detectability, such as:

- Robins (Erithacus rubecula)
- Other resident birds

The focus here is on variation in visibility or activity, rather than presence/absence.

## Why this exists

This modelling work supports the broader goal of the [Field Notes &nearr;](https://davidwalker.uk/) project:

> Turning long-term observations into structured, interpretable insights

By fitting simple models to real data, we can:

- Compare seasonal patterns across species
- Classify types of behaviour (resident, migrant, seasonal)
- Explore changes over time
- Move from description &rarr; explanation
