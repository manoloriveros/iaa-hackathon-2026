#!/bin/sh
# Candidatos de robustez C1 (tope 100.000) y C2 (regularizado), tres semillas, completo y conf (preinscripción CLA-S2-ROBUSTEZ-20261024).
set -x
G="timeout 2400 python3 codigo/desarrollado_gbm.py"
for sd in 11 12 13; do
  for cand in "cap:--cap 100000" "reg:--reg"; do
    nm=${cand%%:*}; op=${cand#*:}
    $G motor --sufijo _rob${nm}s$sd --lr 0.02 --pat 400 --sin make_model --f1 --seed $sd $op
    $G motor --años 2021,2022,2023 --sufijo _rob${nm}confs$sd --lr 0.02 --pat 400 --sin make_model --conf --f1 --seed $sd $op
    for l in contents buildings; do
      $G $l --sufijo _rob${nm}s$sd --lr 0.02 --pat 400 --f1 --seed $sd $op
      $G $l --años 2021,2022,2023 --sufijo _rob${nm}confs$sd --lr 0.02 --pat 400 --conf --f1 --seed $sd $op
    done
  done
done
echo CADENA_TERMINADA
