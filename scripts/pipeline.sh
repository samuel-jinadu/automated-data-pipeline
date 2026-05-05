#!/bin/bash
set -euo pipefail   # stop on error, undefined vars, pipefail

RAWDATA_DIR="../data/raw/"
PROCESSEDDATA_DIR="../data/processed/"
ARCHIVE_DIR="../data/archive/"
ARCHIVELOG_FILEPATH="../logs/archive.log"
PIPELINELOG_FILEPATH="../logs/pipeline.log"
LASTRUNMARKER_FILEPATH="./last_run"


# Archiving – move all previous processed files (except .gitkeep) to archive
shopt -s nullglob
for file in "$PROCESSEDDATA_DIR"*; do
    if [ -f "$file" ] && [ "$(basename "$file")" != ".gitkeep" ]; then
        mv "$file" "$ARCHIVE_DIR"
    fi
done
shopt -u nullglob
cat "$PIPELINELOG_FILEPATH" >> "$ARCHIVELOG_FILEPATH"
./clean-logs.sh


# Main
compgen -G "$RAWDATA_DIR"*.csv > /dev/null && {
    find "$RAWDATA_DIR" -name "*.csv" -newer "$LASTRUNMARKER_FILEPATH" -exec ./pipeline.py "{}" \;
    touch "$LASTRUNMARKER_FILEPATH"
    }


