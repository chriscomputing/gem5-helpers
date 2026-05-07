# Scratchpad

Temporary notes for the current session.

## Immediate Observations

- The repository already includes two example gem5 output directories.
- The main script now acts as a thin wrapper around the reusable library.
- The project metadata now describes the gem5 helpers more accurately.

## Current Ideas

- Keep the dataframe wide, one row per run and one column per stat.
- Keep `run_name` in the batch table so runs are easy to identify.
- Leave values raw rather than adding a normalization layer.
