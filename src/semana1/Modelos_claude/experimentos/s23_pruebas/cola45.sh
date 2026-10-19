#!/bin/bash
# relatividades de severidad acotadas al p99,5 (preinscrito en CLA-20261018-018); GLM sobre partes guardadas, ligero
cd /home/claude/modelos_claude
W=/home/claude/work
python3 -W ignore severidad_cfs.py CFS_motor_4s motor CFSSr_motor --v23=CFS_motor_v23 --v24=CFS_motor_s23 --prod=CFS_motor,CFS_motor_s23 --tope=0.995 >> $W/log_sev_tope.txt 2>&1
python3 -W ignore severidad_cfs.py CFS_buildings buildings CFSS4r_buildings --v24=CFS_buildings,CFS_buildings_s23 --prod=CFS_buildings,CFS_buildings_s23 --tope=0.995 >> $W/log_sev_tope.txt 2>&1
python3 -W ignore severidad_cfs.py FSAP_buildings buildings FSAS4r_buildings --v24=FSAP_buildings,FSAP2_buildings --prod=FSAP_buildings,FSAP2_buildings --tope=0.995 >> $W/log_sev_tope.txt 2>&1
python3 -W ignore severidad_cfs3.py FSAP_contents contents FSAXc4r_contents --v24=FSAP_contents,FSAP2_contents --prod=FSAP_contents,FSAP2_contents --tope=0.995 >> $W/log_sev_tope.txt 2>&1
echo FIN_COLA45 >> $W/log_sev_tope.txt
