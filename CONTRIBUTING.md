# Contributing

## Setup

- Use Python 3.10 or newer.
- Install dependencies with your preferred environment manager.
- The runtime dependency is `pandas`.

## Test Commands

- `python -m unittest discover -s tests`
- `python -m unittest tests.test_analysis tests.test_runs tests.test_stats tests.test_pandas_integration`

## Public API Rules

Public, stability-sensitive surface:

- imports re-exported from `gem5_helpers`
- `Gem5Run`
- the documented `load_runs(...)` dataframe schema and ordering behavior

Internal details may evolve more freely:

- underscore-prefixed helpers
- private validation utilities
- exact internal implementation structure inside modules

When adding a new user-facing capability, export it from `gem5_helpers` and
document it in `README.md`.

## Architecture Notes

The library is intentionally layered:

- `gem5_helpers/stats.py`: parse raw `stats.txt` content into Python mappings
- `gem5_helpers/runs.py`: discover directories, load `config.json` and stats, and normalize data into `Gem5Run`
- `gem5_helpers/analysis.py`: operate on pandas dataframes returned by `load_runs(...)`

Preferred extension pattern:

- add new parsing behavior in `stats.py`
- add new filesystem discovery or run-loading behavior in `runs.py`
- add new dataframe-oriented analysis/reporting helpers in `analysis.py`

Avoid crossing layers when it is not necessary. For example, dataframe shaping
logic should stay out of `stats.py`, and raw parsing details should stay out of
`analysis.py`.

## Adding A New Helper

- decide whether the helper belongs in parsing, loading, or dataframe analysis
- keep raw values unchanged unless the feature explicitly requires a transformation
- prefer additive APIs over breaking changes
- include docstrings, README updates for public helpers, and tests for both happy-path and validation behavior

## Documentation And Tests

- public API additions should update `README.md`
- changes to documented behavior should add or update tests
- dataframe-facing features should have at least one real-pandas integration test
- parser and loader changes should keep unit tests fast and focused
