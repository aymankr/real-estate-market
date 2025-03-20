#!/bin/sh

sleep 5

# Launch the scheduler at given intervals
while true; do
    echo "Starting scheduler"
    poetry run python -m analysis_scheduler

    echo "Sleeping for $START_SCHEDULER_INTERVAL seconds"
    sleep $START_SCHEDULER_INTERVAL
done
