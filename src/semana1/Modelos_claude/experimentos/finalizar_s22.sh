#!/bin/bash
set -e
cd /home/claude/modelos_claude
W=/home/claude/work
FM="motor:1.09:0.95,buildings:1.08:1.14,contents:1.07:1"
F2="motor:1.09:0.95"
python3 -W ignore mezcla3.py S22_claude_propio $W/spec_s22_propio.json --forma=$F2 --nivel=s17 --escribir
python3 -W ignore robustez.py robustez_s22.json S09b=$W/spec_s09b_plano.json S21=$W/spec_s21_propio.json@$FM@s17 S22=$W/spec_s22_propio.json@$F2@s17
python3 -W ignore robustez.py robustez_s22_frente_s21.json S21=$W/spec_s21_propio.json@$FM@s17 S22=$W/spec_s22_propio.json@$F2@s17
python3 -W ignore comparar_codex.py comparar_codex_s22.json $W/spec_s22_propio.json@$F2@s17
python3 -W ignore bootstrap_codex.py bootstrap_codex_s22.json $W/spec_s22_propio.json@$F2@s17
python3 -W ignore publico_simulado.py publico_simulado_s22.json S09b=$W/spec_s09b_plano.json S21=$W/spec_s21_propio.json@$FM@s17 S22=$W/spec_s22_propio.json@$F2@s17
python3 -W ignore influencia_reservas.py influencia_reservas_s22.json S22=$W/spec_s22_propio.json@$F2@s17 S21=$W/spec_s21_propio.json@$FM@s17
python3 -W ignore deriva_nivel.py $W/spec_s22_propio.json deriva_nivel_s22.json
python3 -W ignore calibracion_deciles.py $W/spec_s22_propio.json@$F2@s17 calibracion_deciles_s22.json
python3 -W ignore semestres.py semestres_s22.json S22=$W/spec_s22_propio.json@$F2@s17 S21=$W/spec_s21_propio.json@$FM@s17
python3 -W ignore exportar_predicciones.py s22 S22=$W/spec_s22_propio.json@$F2@s17
echo FIN_FINALIZAR_S22
