#!/bin/bash
set -e
cd /home/claude/ml/codigo
python3 tendencia.py hold
python3 pesos_2025.py 2024
MLIND_BACKBONE=T2 python3 gbm.py hold T1wp
MLIND_BACKBONE=T2b python3 gbm.py hold T3wp
python3 glm.py hold
python3 red.py fino hold contents N3,N2a,N1
python3 red.py fino hold buildings N3,N2a,N1
python3 red.py fino hold motor N3,N2a,N1
echo FIN
