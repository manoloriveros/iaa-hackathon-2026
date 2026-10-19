#!/bin/bash
# severidad híbrida GLM + boosting gamma sobre la frecuencia CatBoost por peligro (CFSG), seis corridas en serie
cd /home/claude/modelos_claude
W=/home/claude/work
for h in 5 2; do
  [ -f $W/CFSG${h}_buildings/resumen.json ] || python3 -W ignore severidad_cfs2.py CFS_buildings buildings CFSG${h}_buildings --hojas=$h >> $W/log_cfsg.txt 2>&1
  [ -f $W/CFSG${h}_contents/resumen.json ] || python3 -W ignore severidad_cfs2.py CFS_contents contents CFSG${h}_contents --hojas=$h >> $W/log_cfsg.txt 2>&1
  [ -f $W/CFSG${h}_motor/resumen.json ] || python3 -W ignore severidad_cfs2.py CFS_motor_4s motor CFSG${h}_motor --v23=CFS_motor_v23 --v24=CFS_motor_s23 --prod=CFS_motor,CFS_motor_s23 --hojas=$h >> $W/log_cfsg.txt 2>&1
done
echo FIN_COLA38 >> $W/log_cfsg.txt
