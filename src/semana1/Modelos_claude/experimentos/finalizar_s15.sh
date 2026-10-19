#!/bin/bash
# S15_claude_propio final: frecuencia CatBoost de autos con cuatro semillas, mezcla, robustez y comparación con A_G/H.
set -e
cd /home/claude/modelos_claude
W=/home/claude/work
FM="motor:1.09:0.95,buildings:1.08:1.14,contents:1.07:1"
python3 combinar_semillas.py CFS_motor_4s CFS_motor CFS_motor_s23
python3 - <<'PY'
import json
s = json.load(open('/home/claude/work/spec_s15_propio.json'))
s['motor'][1] = ["CFS_motor_4s", "CFS_motor", 0.4]
json.dump(s, open('/home/claude/work/spec_s15_final.json', 'w'), indent=1)
print(s)
PY
python3 -W ignore mezcla3.py S15_claude_propio $W/spec_s15_final.json --forma=$FM --escribir
python3 -W ignore robustez.py robustez_s15_final.json S09b=$W/spec_s09b_plano.json S14=$W/spec_s14.json@$FM S15=$W/spec_s15_final.json@$FM
python3 -W ignore comparar_codex.py comparar_codex_s15_final.json $W/spec_s15_final.json@$FM
python3 -W ignore publico_simulado.py publico_simulado_s15_final.json S09b=$W/spec_s09b_plano.json S14=$W/spec_s14.json@$FM S15=$W/spec_s15_final.json@$FM
