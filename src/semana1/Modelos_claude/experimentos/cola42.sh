#!/bin/bash
# dos semillas más de la frecuencia CatBoost de edificios (V24 y 2025 con las iteraciones de V23 de CFS_buildings), en solitario
cd /home/claude/modelos_claude
W=/home/claude/work
[ -f $W/CFS_buildings_s23/prediccion_2025.parquet ] || python3 -W ignore cat_frecsev.py CFS_buildings_s23 buildings --prod --semillas=2 --f3s2 --desde=CFS_buildings --semilla_inicial=2 >> $W/log_cfs_buildings_s23.txt 2>&1
[ -f $W/CFSS4_buildings/resumen.json ] || python3 -W ignore severidad_cfs.py CFS_buildings buildings CFSS4_buildings --v24=CFS_buildings,CFS_buildings_s23 --prod=CFS_buildings,CFS_buildings_s23 >> $W/log_cfs_buildings_s23.txt 2>&1
echo FIN_COLA42 >> $W/log_cfs_buildings_s23.txt
