#!/bin/bash
# LightGBM Tweedie de hogar con tope p99,5 de 2021-22 y recargo uniforme (preinscrito en CLA-20261018-019)
set -e
cd /home/claude/modelos_claude
W=/home/claude/work
python3 -W ignore evaluar.py hT F0124 $W/cfg_hogar_tope.json total buildings,contents > $W/log_hT.txt 2>&1
python3 - <<'PY'
import json
W = "/home/claude/work"
ev = json.load(open(f"{W}/eval_hT.json"))
c = json.load(open(f"{W}/cfg_hogar_tope.json"))
for line in ("buildings", "contents"):
    c[line]["rounds"] = int(ev[line]["best"])
json.dump(c, open(f"{W}/cfg_hogar_tope.json", "w"), indent=1)
print({l: c[l]["rounds"] for l in ("buildings", "contents")})
PY
python3 -W ignore produccion.py S12t_hogar_tope F0124 $W/cfg_hogar_tope.json --solo=buildings,contents --reusar=S08h_hogar_F3s2 --semillas=3 > $W/log_S12t.txt 2>&1
echo FIN_COLA46 >> $W/log_hT.txt
