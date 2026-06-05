#!/bin/bash
# Description: Fetches ROC temperature from LSI 9300-8i
# Requires: storcli

# Run storcli, target controller 0, find the temperature line, and extract the integer
TEMP=$(/path/to/storcli /c0 show all | grep -i "ROC temperature" | awk '{print $4}')

# Output just the number (e.g., 55) for Unraid to parse
echo $TEMP
