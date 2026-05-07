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
  directories beneath a parent directory into one wide dataframe
- `gem5_helpers.mean_stat(frame, stat_name)`: compute the mean of a numeric
  stat column across runs
- `gem5_helpers.min_run_by_stat(frame, stat_name)`: return the run row with the
  minimum value for a numeric stat column
- `gem5_helpers.max_run_by_stat(frame, stat_name)`: return the run row with the
  maximum value for a numeric stat column
- `gem5_helpers.sort_runs_by_stat(frame, stat_name, ascending=True)`: return
  the runs sorted by a numeric stat column
- `analyse_gem5.py`: thin CLI wrapper around `load_runs`

The batch loader includes a `run_name` column for the child directory name and
optionally a `run_path` column for traceability.

The analysis helpers operate on the batch dataframe returned by `load_runs(...)`
and keep raw stat values unchanged.

## Goals

- Parse gem5 output directories in a repeatable way
- Extract useful configuration and statistics data
- Build analysis helpers that can scale to many runs
- Keep the codebase easy to extend as new output patterns appear

## Repository Layout

- `analyse_gem5.py`: command-line entry point
- `gem5_helpers/`: reusable parsing and loading library
- `examples/`: sample gem5 output directories
- `CODEX.md`: durable notes, decisions, and learnings
- `SCRATCHPAD.md`: short-lived working notes

## Working Notes

During this session we will keep two markdown files alongside the code:

- `CODEX.md` for durable project knowledge
- `SCRATCHPAD.md` for temporary notes, hypotheses, and reminders
