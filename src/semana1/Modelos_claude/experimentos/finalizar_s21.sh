#!/bin/bash
set -e
cd /home/claude/modelos_claude
W=/home/claude/work
FM="motor:1.09:0.95,buildings:1.08:1.14,contents:1.07:1"
python3 -W ignore mezcla3.py S21_claude_propio $W/spec_s21_propio.json --forma=$FM --nivel=s17 --escribir
python3 -W ignore robustez.py robustez_s21.json S09b=$W/spec_s09b_plano.json S20=$W/spec_s20_propio.json@$FM@s17 S21=$W/spec_s21_propio.json@$FM@s17
python3 -W ignore robustez.py robustez_s21_frente_s20.json S20=$W/spec_s20_propio.json@$FM@s17 S21=$W/spec_s21_propio.json@$FM@s17
python3 -W ignore comparar_codex.py comparar_codex_s21.json $W/spec_s21_propio.json@$FM@s17
python3 -W ignore bootstrap_codex.py bootstrap_codex_s21.json $W/spec_s21_propio.json@$FM@s17
python3 -W ignore publico_simulado.py publico_simulado_s21.json S09b=$W/spec_s09b_plano.json S20=$W/spec_s20_propio.json@$FM@s17 S21=$W/spec_s21_propio.json@$FM@s17
python3 -W ignore influencia_reservas.py influencia_reservas_s21.json S21=$W/spec_s21_propio.json@$FM@s17 S20=$W/spec_s20_propio.json@$FM@s17
python3 -W ignore deriva_nivel.py $W/spec_s21_propio.json deriva_nivel_s21.json
python3 -W ignore calibracion_deciles.py $W/spec_s21_propio.json@$FM@s17 calibracion_deciles_s21.json
python3 -W ignore semestres.py semestres_s21.json S21=$W/spec_s21_propio.json@$FM@s17 S20=$W/spec_s20_propio.json@$FM@s17
echo FIN_FINALIZAR_S21
