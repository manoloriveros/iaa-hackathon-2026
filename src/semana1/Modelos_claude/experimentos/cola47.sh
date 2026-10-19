#!/bin/bash
# dos semillas nuevas de la frecuencia CatBoost por peligro de autos (V24 y 2025 con las iteraciones V23 de CFS_motor); solo reducen varianza
cd /home/claude/modelos_claude
W=/home/claude/work
[ -f $W/CFS_motor_s45/prediccion_2025.parquet ] || python3 -W ignore cat_frecsev.py CFS_motor_s45 motor --prod --semillas=2 --desde=CFS_motor --semilla_inicial=4 >> $W/log_cfs_motor_s45.txt 2>&1
[ -f $W/CFSS6_motor/resumen.json ] || python3 -W ignore severidad_cfs.py CFS_motor_4s motor CFSS6_motor --v23=CFS_motor_v23 --v24=CFS_motor_s23,CFS_motor_s45 --prod=CFS_motor,CFS_motor_s23,CFS_motor_s45 >> $W/log_cfs_motor_s45.txt 2>&1
echo FIN_COLA47 >> $W/log_cfs_motor_s45.txt
