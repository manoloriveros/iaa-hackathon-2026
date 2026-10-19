#!/bin/bash
set -e
cd /home/claude/modelos_claude
W=/home/claude/work
FM="motor:1.09:0.95,buildings:1.08:1.14,contents:1.07:1"
python3 -W ignore mezcla3.py S20_claude_propio $W/spec_s20_propio.json --forma=$FM --nivel=s17 --escribir
python3 -W ignore robustez.py robustez_s20.json S09b=$W/spec_s09b_plano.json S18=$W/spec_s18_propio.json@$FM@s17 S20=$W/spec_s20_propio.json@$FM@s17
python3 -W ignore robustez.py robustez_s20_frente_s18.json S18=$W/spec_s18_propio.json@$FM@s17 S20=$W/spec_s20_propio.json@$FM@s17
python3 -W ignore comparar_codex.py comparar_codex_s20.json $W/spec_s20_propio.json@$FM@s17
python3 -W ignore bootstrap_codex.py bootstrap_codex_s20.json $W/spec_s20_propio.json@$FM@s17
python3 -W ignore publico_simulado.py publico_simulado_s20.json S09b=$W/spec_s09b_plano.json S18=$W/spec_s18_propio.json@$FM@s17 S20=$W/spec_s20_propio.json@$FM@s17
python3 -W ignore influencia_reservas.py influencia_reservas_s20.json S20=$W/spec_s20_propio.json@$FM@s17 S18=$W/spec_s18_propio.json@$FM@s17
python3 -W ignore deriva_nivel.py $W/spec_s20_propio.json deriva_nivel_s20.json
echo FIN_FINALIZAR_S20
