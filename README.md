# Automated Data Pipeline

A configurable data pipeline that ingests raw CSV data, validates it against user-defined rules, quarantines invalid records, and outputs clean data and metadata — all orchestrated by simple shell scripts, with optional cron scheduling.

## Features

- **Ingestion** – Reads CSV files (UTF‑8, Latin‑1, CP1252) with automatic encoding detection
- **Validation** – Applies YAML‑driven rules (null checks, range checks, regex matching)
- **Quarantine** – Rows failing any rule are moved to a separate file with the violated rule recorded
- **Metadata** – Generates a YAML summary with timestamps, counts, processing time, and warnings
- **Archiving** – Automatically archives old metadata and logs to keep directories clean
- **Scheduling** – Optional cron job to run the pipeline daily at 5 AM
- **Incremental** – Only processes raw CSV files newer than the last run (marker‑based)

## Directory Structure

```
Automated Data Pipeline/
├── data/
│   ├── raw/                # Place incoming CSVs here
│   ├── processed/          # Output: clean data, quarantine file, YAML summary
│   └── archive/            # Old YAML summaries and logs moved here
├── logs/
│   ├── pipeline.log        # Current run log
│   └── archive.log         # Accumulated historical logs
├── scripts/
│   ├── pipeline.py         # Core Python pipeline (ingest + validate + output)
│   ├── pipeline.sh         # Shell wrapper: archive old data, process new CSVs
│   ├── manage.sh           # Install/uninstall the cron job
│   ├── clean-logs.sh       # Clear pipeline.log
│   ├── clean-processed-dir.sh # Remove all processed files
│   ├── rules.yaml          # Validation rules configuration
│   └── last_run            # Timestamp marker for incremental processing
└── README.md
```

## Prerequisites

- **Linux** or **WSL** (the shell scripts use `bash`, `find`, `mv`, etc.)
- **Python 3.10+** with the following packages:
  - `pandas`
  - `pyyaml`
- **crontab** (for scheduling; optional)

Install Python dependencies:

```bash
pip install pandas pyyaml
```

## Setup

1. Clone this repository.
2. Ensure the directory structure exists (the `data/` and `logs/` folders are included).
3. Place your raw CSV files in `data/raw/`. The pipeline expects columns as defined in `rules.yaml`.
4. (Optional) If you are on a system with `systemd`, the cron management script will try to enable and start `cron` automatically – otherwise, you may need to start the cron daemon manually.

## Usage

### Manual Run

From the `scripts/` directory, execute the shell wrapper:

```bash
cd scripts
./pipeline.sh
```

What happens:
- Archiving: moves old processed YAML metadata to `data/archive/` and appends the current pipeline log to `logs/archive.log`, then clears `logs/pipeline.log`.
- Processing: finds any `.csv` files in `data/raw/` that are newer than `scripts/last_run`, runs `pipeline.py` on each, and touches the marker to record the run.

You can also run the Python script directly (useful for testing):

```bash
python pipeline.py ../data/raw/raw.csv
```

### Scheduling (Cron)

To run the pipeline automatically every day at 5 AM:

```bash
./manage.sh install
```

To remove the cron job:

```bash
./manage.sh uninstall
```

Check that your cron daemon is running; `manage.sh` will attempt to start it if not.

## Configuration – `rules.yaml`

All validation rules are defined in a human‑readable YAML file. Each rule specifies:

- `column` – the DataFrame column to check
- `condition` – one of `not_null`, `in_range`, `matches_regex`
- `action` – currently always `quarantine` (skip and fail options are defined but not used)
- Additional parameters: `min`/`max` for `in_range`, `regex` for `matches_regex`

Example (the default rules):

```yaml
rules:
  - column: Postal Code
    condition: matches_regex
    regex: '^\d{5}(?:-\d{4})?$'
    action: quarantine
  - column: Sales
    condition: in_range
    min: 0
    max: 23000
    action: quarantine
  # ... other rules for all columns
```

You can add, remove, or modify rules freely – the pipeline will automatically apply them.

## Outputs

After a successful run, the `data/processed/` folder will contain:

- `processed_YYYYMMDD_HHMMSS.csv` – all valid rows (data that passed every rule)
- `quarantine_YYYYMMDD_HHMMSS.csv` – rows that failed one or more rules, with an extra column `violated_rule` indicating the column and condition that caused the quarantine
- `YYYYMMDD_HHMMSS.yaml` – a summary of the run:

```yaml
Input Filename: ../data/raw/raw.csv
Processing Time: 0.06s
Total Rows Passed: 9545
Total Rows Quarantined: 449
Total Rows Skipped: 0
Total Rules: 13
Total Rules Trigger: 1
Warnings:
- "2026-05-04 15:26:37,890 | Column: 'Postal Code' was quarantined for failing matches_regex!"
```

The YAML file is later moved to `data/archive/` on the next pipeline execution.

## Logging

All pipeline events are logged with timestamps to `logs/pipeline.log`. The log includes:

- Ingestion info (file name, row count)
- Validation steps and any warnings when rules are triggered
- Summary statistics

When `pipeline.sh` runs, it appends the current log to `logs/archive.log` and then clears `pipeline.log`. This keeps the live log concise while preserving history.

## Maintenance

- **Clear logs and processed files** – use the provided clean‑up scripts:
  ```bash
  ./clean-logs.sh
  ./clean-processed-dir.sh
  ```
- **Reset the incremental marker** – delete `scripts/last_run` to reprocess all CSVs on the next run.

## Troubleshooting

- **“No such file” errors** – ensure you are running commands from the `scripts/` directory; all paths are relative.
- **Permission denied** – make sure the shell scripts are executable (`chmod +x *.sh`).
- **Cron job not running** – verify that `cron` is installed and active (`systemctl status cron`); check the cron log for errors.
- **Python import errors** – install the required packages (see Prerequisites) and ensure your Python environment is active.