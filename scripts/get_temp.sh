#!/bin/bash

STORCLI="/usr/local/sbin/storcli"
TMPFILE="/tmp/lsi_temp.txt"

# Bail cleanly if storcli is missing or not executable
if [[ ! -x "$STORCLI" ]]; then
  echo "N/A" > "$TMPFILE"
  exit 1
fi

# Run storcli and capture output; handle command failure
OUTPUT=$("$STORCLI" /c0 show all 2>/dev/null)
if [[ $? -ne 0 || -z "$OUTPUT" ]]; then
  echo "N/A" > "$TMPFILE"
  exit 1
fi

# Extract ROC temp — strip everything except the numeric value
TEMP=$(echo "$OUTPUT" \
  | grep -i "ROC temperature" \
  | grep -oP '=\s*\K[0-9]+')

if [[ -z "$TEMP" ]]; then
  echo "N/A" > "$TMPFILE"
  exit 1
fi

echo "$TEMP" > "$TMPFILE"
