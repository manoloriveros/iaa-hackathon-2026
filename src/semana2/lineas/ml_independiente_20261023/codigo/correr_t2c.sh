#!/bin/bash
set -e
cd /home/claude/ml/codigo
MLIND_BACKBONE=T2c python3 gbm.py dev ninguno
MLIND_BACKBONE=T2c python3 gbm.py hold ninguno
MLIND_BACKBONE=T2c python3 gbm.py pcv ninguno
MLIND_BACKBONE=T2c python3 gbm.py prod ninguno
echo FIN
