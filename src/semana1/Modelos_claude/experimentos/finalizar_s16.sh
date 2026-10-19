#!/bin/bash
set -e
cd /home/claude/modelos_claude
W=/home/claude/work
FM="motor:1.09:0.95,buildings:1.08:1.14,contents:1.07:1"
python3 -W ignore mezcla3.py S16_claude_propio $W/spec_s16_propio.json --forma=$FM --escribir
python3 -W ignore robustez.py robustez_s16.json S09b=$W/spec_s09b_plano.json S14=$W/spec_s14.json@$FM S15=$W/spec_s15_final.json@$FM S16=$W/spec_s16_propio.json@$FM
python3 -W ignore comparar_codex.py comparar_codex_s16.json $W/spec_s16_propio.json@$FM
python3 -W ignore publico_simulado.py publico_simulado_s16.json S09b=$W/spec_s09b_plano.json S14=$W/spec_s14.json@$FM S16=$W/spec_s16_propio.json@$FM
