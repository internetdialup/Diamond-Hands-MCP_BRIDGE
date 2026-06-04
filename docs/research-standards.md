# Research Standards

Use this document to keep analysis artifacts consistent and auditable.

## Data Provenance

Record these details whenever a data source is introduced or changed:

- provider or vendor name
- instrument universe
- timeframe or sampling interval
- timezone assumptions
- schema notes and field definitions
- backfill range and refresh cadence
- any known gaps, revisions, or adjustments

## Indicator and Feature Definitions

Before using an indicator or engineered feature in evaluation, document:

- the exact definition
- parameter values
- source fields used
- preprocessing assumptions
- whether the feature is causal or may leak future information

## Experiment Logging

Each meaningful study in `research/` should capture:

- hypothesis
- dataset and time range
- features or indicators used
- method or evaluation approach
- outcome
- interpretation and next step

## Evaluation Criteria

A strategy idea is not ready to graduate until the research record describes:

- what signal is being tested
- what market regime or asset set it appears to fit
- what failure cases were observed
- whether the result is robust enough to justify implementation work

## Repo Safety

- Do not store secrets in research notes or config examples.
- Keep large raw datasets out of git unless they are deliberately versioned and safe to share.
- Prefer repo-safe config examples and local private data paths.
