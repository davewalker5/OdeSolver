# Wildlife Seasonal Pattern Modelling

This folder contains a set of interpretable mathematical models and supporting analysis tools used to explore seasonal patterns in wildlife observations.

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
- Parameter fitting systems that match models to observed data
- Feature extraction tools that convert fitted models into ecological descriptors
- Species similarity analysis tools for comparing seasonal ecology across taxa

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
- Suitable for downstream ecological analysis

The emphasis is on:

- Clarity over complexity
- Interpretability over optimisation
- Usefulness for natural history observation

### 3. Parameter fitting

The parameter fitting workflow is illustrated below:

![Parameter Fitting](https://github.com/davewalker5/OdeSolver/blob/main/docs/images/parameter-fitting.png?raw=true)

Given observed data (typically monthly presence or detectability), we:

1. Generate a candidate set of model parameters
2. Run the ODE Solver in headless mode
3. Compare the simulated curve to observed data
4. Score the match
5. Repeat to find the best fit

This produces a set of parameters that describe the species’ seasonal behaviour.

### 4. Feature extraction

The feature extraction, similarity and clustering workflow is illustrated below:

![Similarity Analysis and Clustering](https://github.com/davewalker5/OdeSolver/blob/main/docs/images/similarity-analysis.png?raw=true)

Once species have been fitted, the resulting parameter sets and observed seasonal characteristics can be converted into a structured feature matrix.

The feature matrix acts as a common ecological description layer across all species and model families.

Features may include:

- Peak timing
- Seasonal width
- Detectability persistence
- Seasonal symmetry/asymmetry
- Occupancy characteristics
- Classification labels
- Derived ecological traits

The goal is to move from:

> Individual fitted models

into:

> A comparable ecological feature space

This allows species from different model families to be analysed together using a consistent representation.

### 5. Species similarity analysis

The similarity system compares species using weighted ecological distance metrics derived from the feature matrix.

Different feature types are handled differently:

- Circular month features account for year-boundary wrapping
- Numeric features are min-max scaled
- Categorical features use binary matching
- Trait collections use Jaccard distance

The resulting similarity mappings can be used to:

- Identify ecologically similar species
- Explore seasonal guilds and assemblages
- Build nearest-neighbour structures
- Support clustering and dimensionality-reduction workflows
- Compare seasonal structure across unrelated taxa
- Investigate phenological synchrony within the wider ecological community

Importantly, similarity in this system does not necessarily imply taxonomic similarity or direct biological interaction.

Instead, the system primarily measures similarity of seasonal ecological signal — shared timing structure, seasonal occupancy, detectability dynamics, flowering periods, migration windows, emergence timing, and other temporally expressed ecological behaviours.

This allows comparisons not only within groups (e.g. bird-to-bird or plant-to-plant), but also across domains of the ecosystem. For example, a butterfly flight period may align strongly with flowering periods or migratory arrival windows, potentially revealing shared seasonal forcing, phenological synchrony, or broader ecological coupling.

As a result, the similarity system can be viewed not simply as a species comparison tool, but as a framework for analysing the seasonal structure of the ecological community as a whole.

A key design goal is interpretability.

Rather than producing opaque embeddings or black-box similarity scores, the system attempts to preserve ecological meaning at every stage of the comparison process. Component distances remain inspectable, allowing similarities to be understood in terms of timing, amplitude, seasonal width, suppression dynamics, classification structure, and trait overlap.

### 6. Cluster and neighbourhood analysis

Once pairwise species similarity has been calculated, the resulting similarity matrix can be explored using hierarchical clustering, dendrogram analysis, and heatmap visualisation techniques. 

The dendrogram visualisation exposes the hierarchy directly, allowing seasonal ecological neighbourhoods and nested sub-structure to be explored across multiple scales simultaneously.

The clustering system attempts to identify groups of species occupying similar regions of seasonal ecological space.

These neighbourhoods are not intended to represent strict taxonomic groupings. Instead, they reflect similarities in seasonal ecological signal, including:

- Shared timing structure
- Similar seasonal persistence
- Comparable detectability behaviour
- Overlapping flowering, emergence, or migration periods
- Broad phenological synchrony

The resulting clusters often contain ecologically plausible seasonal assemblages, including:

- Resident bird neighbourhoods
- Spring flowering communities
- Butterfly flight-period groupings
- Transitional seasonal assemblages
- More isolated winter visitor behaviour

Importantly, the clustering structure is hierarchical rather than absolute.

The heatmaps, dendrograms, and extracted clusters should therefore be interpreted as exploratory views of seasonal ecological structure rather than fixed ecological categories.

A major design goal remains interpretability.

Cluster summaries attempt to expose the underlying feature structure driving the groupings, including:

- Dominant classifications
- Shared traits
- Mean seasonal timing
- Seasonal width
- Distinguishing ecological characteristics

This allows the resulting neighbourhoods to be inspected and interpreted ecologically, rather than treated as opaque statistical groupings.

The resulting neighbourhood structures can also be aggregated temporally to produce seasonal ecological calendars that summarise the mean normalised activity of ecological neighbourhoods across the year, allowing broader seasonal structure to be visualised at community scale rather than species-by-species.

Rather than focusing on individual taxa, the calendars attempt to expose larger seasonal ecological modes, including:

- Winter visitor structure
- Spring flowering and emergence periods
- Resident detectability dynamics
- Extended summer assemblages
- Transitional seasonal neighbourhoods

The resulting heatmaps provide an interpretable view of how different regions of seasonal ecological space become active, overlap, and decline through the ecological year.

## Folder Structure

### seasonal-presence/

Models species that are absent outside a defined season, where that season doesn't wrap the boundaries of the year, such as:

- Swifts (Apus apus)
- Swallows (Hirundo rustica)
- Flowering plants such as the bluebell (Hyacinthoides non-scripta)

The _data/_ sub-folder contains the observed and simulated data, consensus parameter file and classification file for each species modelled using the seasonal model. The _model/_ sub-folder contains the ODE Solver simulation file and an extracted version of the models Python script. 

### winter-visitor/

Models species that are absent outside the autumn/winter season, such as:

- Redwing (Turdus iliacus)
- Fieldfare (Turdus pilaris)

The _data/_ sub-folder contains the observed and simulated data, consensus parameter file and classification file for each species modelled using the seasonal model. The _model/_ sub-folder contains the ODE Solver simulation file and an extracted version of the models Python script.

### resident-detectability/

Models species that are present year-round, but vary in detectability, such as:

- Robins (Erithacus rubecula)
- Other resident birds

The focus here is on variation in visibility or activity, rather than presence/absence.

The _data/_ sub-folder contains the observed and simulated data, consensus parameter file and classification file for each species modelled using the seasonal model. The _model/_ sub-folder contains the ODE Solver simulation file and an extracted version of the models Python script.

### data/

Contains the feature matrices and species similarity artifacts.

## Why this exists

This modelling work supports the broader goal of the [Field Notes &nearr;](https://davidwalker.uk/) project:

> Turning long-term observations into structured, interpretable insights

By fitting simple models to real data, we can:

- Compare seasonal patterns across species
- Classify types of behaviour (resident, migrant, seasonal)
- Explore ecological similarity and grouping
- Analyse seasonal structure at community scale
- Explore changes over time
- Move from description &rarr; explanation


## Design philosophy

This project intentionally favours:

- Interpretable models over highly optimised black-box approaches
- Ecological meaning over abstract statistical performance
- Transparent calculations over opaque pipelines
- Long-term maintainability over rapid experimentation

The aim is not simply to generate predictions, but to build a computational natural history framework that remains understandable, inspectable, and scientifically interpretable.
