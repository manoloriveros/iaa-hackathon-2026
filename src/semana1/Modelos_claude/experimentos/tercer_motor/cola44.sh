#!/bin/bash
# tercer motor de frecuencia en autos (preinscrito en CLA-20261018-011): espera a que termine cola43 y corre solo
while kill -0 610 2>/dev/null; do sleep 15; done
cd /home/claude/modelos_claude
W=/home/claude/work
[ -f $W/FS2P_motor/prediccion_2025.parquet ] || python3 -W ignore frecsev2.py FS2P_motor motor --prod --semillas=2 --partes >> $W/log_fs2p_motor.txt 2>&1
[ -f $W/FS2S_motor/resumen.json ] || python3 -W ignore severidad_cfs.py FS2P_motor motor FS2S_motor >> $W/log_fs2p_motor.txt 2>&1
echo FIN_COLA44 >> $W/log_fs2p_motor.txt
