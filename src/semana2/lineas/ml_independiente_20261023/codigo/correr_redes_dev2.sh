#!/bin/bash
cd /home/claude/ml/codigo
for l in contents buildings motor; do python3 red.py fino dev $l N2b,N3,N2a,N1; done
echo FIN
