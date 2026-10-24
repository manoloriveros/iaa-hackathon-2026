#!/bin/sh
# Reentrenos tras corregir ID01 en variables.py (solo cambia autos del desarrollado) y corridas pendientes.
set -x
G="timeout 2400 python3 codigo/desarrollado_gbm.py"
for sd in 11 12 13; do
  $G motor --sufijo _v2fixs$sd --lr 0.02 --pat 400 --sin make_model --seed $sd
  $G motor --años 2021,2022,2023 --sufijo _v2fixconfs$sd --lr 0.02 --pat 400 --sin make_model --conf --seed $sd
done
for sd in 12 13; do for l in contents buildings; do
  $G $l --años 2021,2022,2023 --sufijo _v2confs$sd --lr 0.02 --pat 400 --conf --seed $sd
done; done
for l in contents buildings; do
  $G $l --sufijo _v2f1 --lr 0.02 --pat 400 --f1
  $G $l --años 2021,2022,2023 --sufijo _v2f1conf --lr 0.02 --pat 400 --conf --f1
done
$G motor --sufijo _v2fixf1 --lr 0.02 --pat 400 --sin make_model --f1
$G motor --años 2021,2022,2023 --sufijo _v2fixf1conf --lr 0.02 --pat 400 --sin make_model --conf --f1
timeout 3000 python3 codigo/p1_escalera.py motor
timeout 3000 python3 codigo/p1_escalera.py motor --f1
echo CADENA_TERMINADA
