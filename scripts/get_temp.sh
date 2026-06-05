#!/bin/bash
# Fetch temperature and isolate the number after the equals sign
TEMP=$(/usr/local/sbin/storcli /c0 show all | grep -i "ROC temperature" | awk -F'=' '{print $2}' | tr -d ' ')

# Save to RAM-disk file for the GUI to read instantly
echo $TEMP > /tmp/lsi_temp.txt
