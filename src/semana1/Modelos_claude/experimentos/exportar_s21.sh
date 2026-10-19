#!/bin/bash
set -e
cd /home/claude/modelos_claude
W=/home/claude/work
FM="motor:1.09:0.95,buildings:1.08:1.14,contents:1.07:1"
python3 -W ignore exportar_predicciones.py s21 S21=$W/spec_s21_propio.json@$FM@s17
python3 -W ignore semestres.py semestres_s21.json S21=$W/spec_s21_propio.json@$FM@s17 S20=$W/spec_s20_propio.json@$FM@s17
echo FIN_EXPORTAR_S21
