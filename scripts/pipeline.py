#!/usr/bin/env python


import pandas as pd
import yaml
import logging
import sys
from pathlib import Path
import time
from datetime import datetime



LOG_FORMAT = "%(asctime)s | %(levelname)s | %(message)s"
WARN_FORMAT = "%(asctime)s | %(message)s"
LOGFILEPATH = "../logs/pipeline.log"
RAWDATAPATH = Path(sys.argv[1]) if len(sys.argv) == 2 else sys.exit(print(f"Usage: python {sys.argv[0]} <filepath>") or 1)
YAMLRULESPATH = "./rules.yaml"
PROCESSEDDATADIR = "../data/processed/"
TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
PROCESSEDDATAFILEPATH = f"{PROCESSEDDATADIR}processed_{TIMESTAMP}.csv"
QUARANTINEDATAFILEPATH = f"{PROCESSEDDATADIR}quarantine_{TIMESTAMP}.csv"
METADATAFILEPATH = f"{PROCESSEDDATADIR}{TIMESTAMP}.yaml"

class WarningsCollector(logging.Handler):
    def __init__(self):
        super().__init__(level = logging.WARNING)
        self.setFormatter(logging.Formatter(WARN_FORMAT))
        self.warnings = []

    def emit(self, record):
        self.warnings.append(self.format(record))

collector = WarningsCollector()

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOGFILEPATH),
        logging.StreamHandler(),
        collector
    ]
)
logger = logging.getLogger(__name__)
info = logger.info
error = logger.error
warning = logger.warning


def infobar(title):
    info("=" * 50)
    info(title.upper())
    info("=" * 50)
    return 0


def ingest(path):
    infobar("Ingestion starts!")
    path = Path(path)
    path = path if path.exists() else sys.exit(error(f"{path.name} does not exist!") or 1)

    def loadcsv(path):
        for enc in ['utf-8', 'latin-1', 'cp1252']:
            try:
                df = pd.read_csv(path, encoding=enc)
                return df
            except UnicodeDecodeError:
                continue   # next encoding
            except pd.errors.ParserError:
                # This isn't an encoding issue; try to skip bad lines
                df = pd.read_csv(path, encoding=enc, on_bad_lines='skip')
                return df
            except Exception:
                error(f"'{Exception}' happened when trying to read csv!")
                brokenpipeline()
    
    df = loadcsv(path)    
    
    info(f"'{path.name}' has {df.shape[0]} rows!")
    infobar("Ingestion complete!")
    return df

def brokenpipeline():
    error("If you are reading this the pipelne has broken for whatever reason, its too late, save yourself!")
    sys.exit(1)

def validate(df, rules_path):
    infobar("Validation begins!")
    start = time.perf_counter()
    valid_df = df
    quarantined_df = pd.DataFrame()
    skipped_df = pd.DataFrame()

    def quarantine(column, condition, mask):
        nonlocal quarantined_df
        warning(f"Column: '{column}' was quarantined for failing {condition}!")
        quarantined_chunk = valid_df[mask].copy()
        quarantined_chunk['violated_rule'] = f"{column} | {condition}"
        quarantined_df = pd.concat([quarantined_chunk, quarantined_df], ignore_index=True)
        return valid_df[~mask].copy()
    
    def skip(column, condition, mask):
        nonlocal skipped_df
        warning(f"Column: '{column}' was skipped for failing {condition}!")
        skipped_chunk = valid_df[mask].copy()
        skipped_df = pd.concat([skipped_df, skipped_chunk], ignore_index=True)
        return valid_df[~mask].copy()
    
    def fail(column, condition, mask):
        error(f"Column: '{column}' has broken the pipeline for failing {condition}!")
        failed_chunk = valid_df[mask].copy()
        error(failed_chunk.head())
        return brokenpipeline()
    
    def act(action, column, condition, mask):
        match action:
            case "quarantine":
                return quarantine(column, condition, mask)
            case "skip":
                return skip(column, condition, mask)
            case "fail":
                return fail(column, condition, mask)


    with open(rules_path, 'r') as f:
        rule_data = yaml.safe_load(f)
        rules = rule_data['rules']
        rules_trigger_counter = 0
        conditions = rule_data["conditions"]

        for rule in rules:
            column = rule["column"]
            column_df = valid_df[column]
            condition = rule["condition"]
             
            action = rule["action"]

            match condition:
                case "not_null":
                    null_series = column_df.isnull()
                    if null_series.any():
                        valid_df = act(action, column, condition, mask=null_series)
                        rules_trigger_counter += 1
                case "in_range":
                    min = rule["min"]
                    max = rule["max"]
                    not_in_range_series = ~column_df.between(min, max)
                    if not_in_range_series.any():
                        valid_df = act(action, column, condition, mask=not_in_range_series)
                        rules_trigger_counter += 1
                case "matches_regex":
                    regex = rule["regex"]
                    not_match_series = ~column_df.astype(str).str.match(regex)
                    # todo
                    if not_match_series.any():
                        valid_df = act(action, column, condition, mask=not_match_series)
                        rules_trigger_counter += 1
        # summary
        summary = {
            "Total Rows Processed": len(df),
            "Total Rows Passed": len(valid_df),
            "Total Rows Quarantined": len(quarantined_df),
            "Total Rows Skipped": len(skipped_df),
            "Total Rules": len(rules),
            "Total Rules Trigger": rules_trigger_counter,
            "Processing Time": f"{time.perf_counter() - start:.2f}s"
        }
        infobar("Summary begins!")
        info(summary)
        infobar("Summary ends!")

    infobar("Validation ends!")
    return {
        "valid": valid_df,
        "quarantine": quarantined_df,
        "summary": summary,
    }

def main():
    results = validate(ingest(RAWDATAPATH), YAMLRULESPATH)
    
    results["valid"].to_csv(PROCESSEDDATAFILEPATH, index=False)
    results["quarantine"].to_csv(QUARANTINEDATAFILEPATH)
    results["summary"]["Input Filename"] = RAWDATAPATH
    results["summary"]["Warnings"] = collector.warnings

    with open(METADATAFILEPATH, "w") as f:
        yaml.dump(results["summary"], f)


if __name__ == "__main__":
    sys.exit(main())