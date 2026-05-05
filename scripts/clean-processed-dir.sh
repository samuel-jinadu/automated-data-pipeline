#!/bin/bash

# Remove all files except .gitkeep (so the empty folder stays in git)
find ../data/processed/ -type f -not -name '.gitkeep' -delete
echo "Processed files removed (.gitkeep preserved)"