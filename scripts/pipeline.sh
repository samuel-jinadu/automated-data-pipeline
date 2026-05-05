#!/bin/bash
set -euo pipefail   # stop on error, undefined vars, pipefail

RAWDATA_DIR="../data/raw/"
PROCESSEDDATA_DIR="../data/processed/"
ARCHIVE_DIR="../data/archive/"
ARCHIVELOG_FILEPATH="../logs/archive.log"
PIPELINELOG_FILEPATH="../logs/pipeline.log"
LASTRUNMARKER_FILEPATH="./last_run"


# Archiving
compgen -G "$PROCESSEDDATA_DIR"*.yaml > /dev/null && mv "$PROCESSEDDATA_DIR"*.yaml "$ARCHIVE_DIR"
cat "$PIPELINELOG_FILEPATH" >> "$ARCHIVELOG_FILEPATH"
./clean-logs.sh


# Main
compgen -G "$RAWDATA_DIR"*.csv > /dev/null && {
    find "$RAWDATA_DIR" -name "*.csv" -newer "$LASTRUNMARKER_FILEPATH" -exec ./pipeline.py "{}" \;
    touch "$LASTRUNMARKER_FILEPATH"
    }


