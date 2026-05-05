#!/bin/bash
set -euo pipefail   # stop on error, undefined vars, pipefail

# Ensure cron service is running
if ! systemctl is-active --quiet cron; then
    echo "Starting cron..."
    sudo systemctl enable --now cron
fi

# cron job
CRONJOB='0 5 * * * "/mnt/c/Users/Samuel/Desktop/Remote Job/practice/resume projects/Automated Data Pipeline/scripts/pipeline.sh" >> "/mnt/c/Users/Samuel/Desktop/Remote Job/practice/resume projects/Automated Data Pipeline/logs/bash.log" 2>&1'


install() {
    crontab -l 2>/dev/null | grep -F "$CRONJOB" && echo "Cron job already exists" || {
        echo "Adding cron job..."
        (crontab -l 2>/dev/null; echo "$CRONJOB") | crontab -
        echo "Cron job installed."
    }
}


uninstall() {
    crontab -l 2>/dev/null | grep -F -v "$CRONJOB" | crontab -
    echo "Cron job removed."
}

case "${1:-}" in
    install)            install ;;
    uninstall)        uninstall ;;
    *)                     echo "Usage $0 <install/uninstall>" ;;
esac

