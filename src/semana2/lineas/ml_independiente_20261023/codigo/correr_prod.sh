#!/bin/bash
set -e
cd /home/claude/ml/codigo
MLIND_BACKBONE=T2b python3 gbm.py pcv T3wp
MLIND_BACKBONE=T2b python3 gbm.py prod T3wp
python3 tendencia.py prod
echo FIN
