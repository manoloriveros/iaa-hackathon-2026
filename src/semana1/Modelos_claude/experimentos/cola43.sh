#!/bin/bash
# frecuencia LightGBM por peligro de profundidad intermedia (frecsev2 sin --aditivo) con partes, y severidad GLM encima
while kill -0 196 2>/dev/null; do sleep 15; done
cd /home/claude/modelos_claude
W=/home/claude/work
for L in buildings contents; do
  [ -f $W/FS2P_$L/prediccion_2025.parquet ] || python3 -W ignore frecsev2.py FS2P_$L $L --prod --semillas=2 --partes >> $W/log_fs2p.txt 2>&1
done
[ -f $W/FS2S_buildings/resumen.json ] || python3 -W ignore severidad_cfs.py FS2P_buildings buildings FS2S_buildings >> $W/log_fs2p.txt 2>&1
[ -f $W/FS2Xc_contents/resumen.json ] || python3 -W ignore severidad_cfs3.py FS2P_contents contents FS2Xc_contents >> $W/log_fs2p.txt 2>&1
echo FIN_COLA43 >> $W/log_fs2p.txt
