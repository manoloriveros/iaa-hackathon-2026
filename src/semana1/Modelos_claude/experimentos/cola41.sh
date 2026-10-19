#!/bin/bash
# autos: V24 y 2025 de la frecuencia aditiva con partes (la corrida FSAP_motor murió por memoria tras V23), en solitario
cd /home/claude/modelos_claude
W=/home/claude/work
[ -f $W/FSAP_motor_b/prediccion_2025.parquet ] || python3 -W ignore frecsev2.py FSAP_motor_b motor --prod --semillas=2 --aditivo --partes --desde=FSAP_motor --semilla_inicial=0 >> $W/log_fsap_motor_b.txt 2>&1
[ -f $W/FSAS_motor/resumen.json ] || python3 -W ignore severidad_cfs.py FSAP_motor motor FSAS_motor --v24=FSAP_motor_b --prod=FSAP_motor_b >> $W/log_fsap_motor_b.txt 2>&1
echo FIN_COLA41 >> $W/log_fsap_motor_b.txt
