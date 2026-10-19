#!/bin/bash
while kill -0 2186 2>/dev/null; do sleep 10; done
cd /home/claude/modelos_claude
W=/home/claude/work
[ -f $W/sel_CFS_motor_v23.parquet ] || python3 -W ignore cat_frecsev.py CFS_motor_v23 motor >> $W/log_cfs_motor_v23.txt 2>&1
