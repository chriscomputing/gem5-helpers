# gem5-helpers

Tools for programmatically analyzing large amounts of gem5 simulation output.

The first target for this project is to read simulation result directories that
contain at least:

- `config.json`: the full CPU and system configuration
- `stats.txt`: the simulation statistics gathered during execution

Example outputs live under `examples/`.

## Current API

- `gem5_helpers.load_run(path, dump_index=0)`: load one run directory
- `gem5_helpers.load_runs(parent_dir, dump_index=0)`: load all valid run
  directories beneath a parent directory into one pandas dataframe
- `gem5_helpers.list_run_names(frame)`: list run names in dataframe row order
- `gem5_helpers.list_stat_names(frame)`: list stat columns in dataframe column
  order
- `gem5_helpers.select_runs(frame, run_names=None, stat_names=None)`: filter
  the batch dataframe down to selected runs and stat columns while preserving
  metadata columns
- `gem5_helpers.mean_stat(frame, stat_name)`: compute the mean of a numeric
  stat column across runs
- `gem5_helpers.min_run_by_stat(frame, stat_name)`: return the run row with the
  minimum value for a numeric stat column
- `gem5_helpers.max_run_by_stat(frame, stat_name)`: return the run row with the
  maximum value for a numeric stat column
- `gem5_helpers.sort_runs_by_stat(frame, stat_name, ascending=True)`: return
  the runs sorted by a numeric stat column
- `gem5_helpers.build_run_report(frame, stat_names, run_names=None)`: select a
  narrow run report containing `run_name` plus chosen stat columns
- `gem5_helpers.render_run_report_markdown(...)`: render a selected run report
  as a Markdown table
- `gem5_helpers.render_run_report_csv(...)`: render a selected run report as
  CSV text
- `analyse_gem5.py`: thin CLI wrapper around `load_runs`

The batch loader includes a `run_name` column for the child directory name and
optionally a `run_path` column for traceability.

The analysis helpers operate on the batch dataframe returned by `load_runs(...)`
and keep raw stat values unchanged.

## Dataframe Contract

`load_runs(...)` returns a pandas `DataFrame`. That is part of the public API.

Documented schema:

- one row per discovered run directory
- `run_name`: required, child directory name
- `dump_index`: required, zero-based selected stats dump index
- `run_path`: optional, included unless `include_run_path=False`
- stat columns: one column per parsed gem5 stat, in first-seen order across runs

Behavior guarantees:

- row order follows sorted child-directory names on disk
- `run_name` values identify runs for selection and reporting
- missing stats remain missing in the dataframe and may appear as `NaN`
- analysis helpers preserve raw stat values and do not normalize them

## Custom Analysis Script

```python
from gem5_helpers import (
    list_run_names,
    list_stat_names,
    load_runs,
    mean_stat,
    render_run_report_markdown,
    select_runs,
    sort_runs_by_stat,
)

frame = load_runs("examples", include_run_path=False)

available_runs = list_run_names(frame)
available_stats = list_stat_names(frame)

selected = select_runs(
    frame,
    run_names=["default_op2_loop0", "config1_loop1"],
    stat_names=["simSeconds", "simTicks"],
)

fastest_first = sort_runs_by_stat(selected, "simSeconds")
mean_sim_seconds = mean_stat(selected, "simSeconds")

markdown_table = render_run_report_markdown(
    selected,
    stat_names=["simSeconds", "simTicks"],
)
```

Use `select_runs(...)` when you want a dataframe that is still convenient for
custom pandas work. Use `build_run_report(...)` or the render helpers when you
want a narrow export-oriented view.

## Reporting Example

```python
from gem5_helpers import (
    load_runs,
    render_run_report_csv,
    render_run_report_markdown,
)

frame = load_runs("examples", include_run_path=False)
run_names = ["default_op2_loop0", "config1_loop1"]
stat_names = ["simSeconds", "simTicks"]

markdown_table = render_run_report_markdown(
    frame,
    stat_names=stat_names,
    run_names=run_names,
)

csv_text = render_run_report_csv(
    frame,
    stat_names=stat_names,
    run_names=run_names,
)
```

## API Stability

Stable public API:

- functions and classes exported from `gem5_helpers`
- the `Gem5Run` dataclass
- the documented `load_runs(...)` dataframe contract above

Internal implementation details:

- underscore-prefixed helpers inside modules
- exact internal organization within `analysis.py`, `runs.py`, and `stats.py`
- test doubles and test-only helpers

If you are writing custom scripts, prefer importing from `gem5_helpers` rather
than deep-importing private helpers from submodules.

## Goals

- Parse gem5 output directories in a repeatable way
- Extract useful configuration and statistics data
- Build analysis helpers that can scale to many runs
- Keep the codebase easy to extend as new output patterns appear

## Repository Layout

- `analyse_gem5.py`: command-line entry point
- `gem5_helpers/stats.py`: raw stats parsing into Python data structures
- `gem5_helpers/runs.py`: run discovery/loading into `Gem5Run` and batch frames
- `gem5_helpers/analysis.py`: pandas-based analysis and reporting helpers
- `examples/`: sample gem5 output directories
- `CONTRIBUTING.md`: contributor workflow and extension guidance
- `CODEX.md`: durable notes, decisions, and learnings
- `SCRATCHPAD.md`: short-lived working notes

## Working Notes

During this session we will keep two markdown files alongside the code:

- `CODEX.md` for durable project knowledge
- `SCRATCHPAD.md` for temporary notes, hypotheses, and reminders
