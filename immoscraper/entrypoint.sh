#!/bin/sh

SPIDERS=$(echo "$SCRAPS" | tr ',' ' ')
TIMES=$(echo "$SCRAPS_RUN_TIMES" | tr ',' ' ')

# Print current time
echo "[$(date)] Starting scheduling loop"

# Print the spiders and their run times
echo "[$(date)] Spiders to run: $SPIDERS"
echo "[$(date)] Run times: $TIMES"

while true; do
    echo "Checking current time $(date)"

    CURRENT_TIME=$(date)
    for time in $TIMES; do
        # if current time is equal (60 seconds margin) to the time in the list
        if [ $(date -d "$time" +%s) -le $(date -d "$CURRENT_TIME" +%s) ] && [ $(date -d "$time" +%s) -ge $(date -d "$CURRENT_TIME -60 seconds" +%s) ]; then
            for spider in $SPIDERS; do
                echo "[$(date)] Running spider $spider"
                poetry run scrapy crawl $spider
            done
        fi
    done
    sleep 60
done
