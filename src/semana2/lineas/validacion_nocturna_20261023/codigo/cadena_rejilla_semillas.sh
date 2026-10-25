#!/bin/sh
# ROB-C4: semillas 12 y 13 (completa) y 11-13 (conf) de las configuraciones elegidas por la validación interna:
# edificios G2 y contenidos G5; autos se queda en C2.
set -x
G="timeout 2400 python3 codigo/desarrollado_gbm.py"
G2='{"num_leaves":7,"min_data_in_leaf":5000,"lambda_l2":100,"feature_fraction":0.7}'
G5='{"num_leaves":15,"min_data_in_leaf":3000,"lambda_l2":200,"feature_fraction":0.5}'
for sd in 12 13; do
  $G buildings --sufijo _rejG2s$sd --lr 0.02 --pat 400 --f1 --seed $sd --params "$G2"
  $G contents --sufijo _rejG5s$sd --lr 0.02 --pat 400 --f1 --seed $sd --params "$G5"
done
for sd in 11 12 13; do
  $G buildings --años 2021,2022,2023 --sufijo _rejG2confs$sd --lr 0.02 --pat 400 --conf --f1 --seed $sd --params "$G2"
  $G contents --años 2021,2022,2023 --sufijo _rejG5confs$sd --lr 0.02 --pat 400 --conf --f1 --seed $sd --params "$G5"
done
echo CADENA_TERMINADA
