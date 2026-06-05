#!/bin/bash
# Fetch temperature using the storcli symlink we created
TEMP=$(/usr/local/sbin/storcli /c0 show all | grep -i "ROC temperature" | awk '{print $4}')

# Save to RAM-disk file for the GUI to read instantly
echo $TEMP > /tmp/lsi_temp.txt
