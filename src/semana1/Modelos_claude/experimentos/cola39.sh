#!/bin/bash
# frecuencia aditiva (árboles de una división) con partes por peligro y severidad GLM por capital/valor (FSAS)
cd /home/claude/modelos_claude
W=/home/claude/work
for L in buildings contents motor; do
  [ -f $W/FSAP_$L/prediccion_2025.parquet ] || python3 -W ignore frecsev2.py FSAP_$L $L --prod --semillas=2 --aditivo --partes >> $W/log_fsap.txt 2>&1
  if [ $L = motor ]; then
    [ -f $W/FSAS_$L/resumen.json ] || python3 -W ignore severidad_cfs.py FSAP_$L $L FSAS_$L >> $W/log_fsap.txt 2>&1
  else
    [ -f $W/FSAS_$L/resumen.json ] || python3 -W ignore severidad_cfs.py FSAP_$L $L FSAS_$L >> $W/log_fsap.txt 2>&1
  fi
done
echo FIN_COLA39 >> $W/log_fsap.txt
