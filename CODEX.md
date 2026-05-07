# CODEX Notes

This file stores durable project knowledge that should remain useful across the
session and future work.

## Project Scope

- Analyze gem5 simulation output directories.
- Focus on `config.json` and `stats.txt` as the primary inputs.
- Use the `examples/` directories as the initial reference data.

## Working Assumptions

- Each simulation output directory is expected to be self-contained.
- `config.json` describes the simulation setup.
- `stats.txt` contains numeric results and counters collected during the run.

## Decisions

- Keep the project documentation in plain Markdown files at the repository root.
- Use `README.md` for the project overview and `CODEX.md` for long-lived notes.
- Use `SCRATCHPAD.md` only for temporary notes that can be discarded later.
- The library exposes both `load_run(...)` and `load_runs(...)`.
- Batch loading is one level deep below the provided parent directory.
- Batch dataframes are wide, with one row per run and a `run_name` column.
- `dump_index` is zero-based and defaults to the first stats dump.
- The analysis layer should preserve raw stat values and should not normalize
  the data.
- The first analysis helpers are dataframe-based and accept a stat name as a
  string column selector.
- The initial analysis API includes mean, min-run, max-run, and sorted-runs
  helpers.
- Extrema helpers return the full run row rather than only the scalar value.
