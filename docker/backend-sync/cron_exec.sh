#!/bin/sh
cd /usr/local/scripts/
source .env
# write new date into log before run update
echo "====================================="
DT=$(date)
echo ${DT}
echo "====================================="
/usr/local/bin/python3 update_indicators.py
