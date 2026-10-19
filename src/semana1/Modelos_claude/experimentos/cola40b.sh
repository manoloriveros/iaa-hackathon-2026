#!/bin/bash
# semillas nuevas de la frecuencia aditiva (2 más) para promediar en FSAS de hogar
# arranca en paralelo con la cola 39
cd /home/claude/modelos_claude
W=/home/claude/work
for L in buildings contents; do
  [ -f $W/FSAP2_$L/prediccion_2025.parquet ] || python3 -W ignore frecsev2.py FSAP2_$L $L --prod --semillas=2 --aditivo --partes --desde=FSAP_$L --semilla_inicial=2 >> $W/log_fsap2.txt 2>&1
  [ -f $W/FSAS4_$L/resumen.json ] || python3 -W ignore severidad_cfs.py FSAP_$L $L FSAS4_$L --v24=FSAP_$L,FSAP2_$L --prod=FSAP_$L,FSAP2_$L >> $W/log_fsap2.txt 2>&1
done
echo FIN_COLA40 >> $W/log_fsap2.txt
