#!/bin/sh
# Semillas 12 y 13 del GBM desarrollado con historia F1 (completo 2021-2024 y conf 2021-2023), para A1fixF1b3.
set -x
G="timeout 2400 python3 codigo/desarrollado_gbm.py"
for sd in 12 13; do
  $G motor --sufijo _v2fixf1s$sd --lr 0.02 --pat 400 --sin make_model --f1 --seed $sd
  $G motor --años 2021,2022,2023 --sufijo _v2fixf1confs$sd --lr 0.02 --pat 400 --sin make_model --conf --f1 --seed $sd
  for l in contents buildings; do
    $G $l --sufijo _v2f1s$sd --lr 0.02 --pat 400 --f1 --seed $sd
    $G $l --años 2021,2022,2023 --sufijo _v2f1confs$sd --lr 0.02 --pat 400 --conf --f1 --seed $sd
  done
done
echo CADENA_TERMINADA
