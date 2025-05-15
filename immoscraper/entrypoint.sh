#!/bin/sh

SPIDERS=$(echo "$SCRAPS" | tr ',' ' ')
TIMES=$(echo "$SCRAPS_RUN_TIMES" | tr ',' ' ')

# Print current time
echo "[$(date)] Starting scheduling loop"

# Print the spiders and their run times
echo "[$(date)] Spiders to run: $SPIDERS"
echo "[$(date)] Run times: $TIMES"

# Run the spiders immediately on startup
echo "[$(date)] Running spiders immediately on startup"
for spider in $SPIDERS; do
    echo "[$(date)] Running spider $spider"
    poetry run scrapy crawl $spider
done

while true; do
    # Current time format: HH:MM
    CURRENT_TIME=$(date +"%H:%M")
    echo "[$(date)] Checking current time: $CURRENT_TIME"

    for time in $TIMES; do
        # Compare time strings directly (HH:MM)
        if [ "$CURRENT_TIME" = "$time" ]; then
            echo "[$(date)] Time match: $CURRENT_TIME = $time"
            for spider in $SPIDERS; do
                echo "[$(date)] Running spider $spider"
                poetry run scrapy crawl $spider
            done
        fi
    done
    
    # Wait for a minute before checking again
    sleep 60
done
