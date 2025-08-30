#!/bin/bash
# Rotate logs to prevent them from getting too large
cd "$(dirname "$0")"
if [ -f "logs/cron.log" ] && [ $(stat -f%z "logs/cron.log") -gt 10485760 ]; then
    mv logs/cron.log "logs/cron.log.$(date +%Y%m%d_%H%M%S)"
    echo "Log rotated at $(date)" > logs/cron.log
fi
