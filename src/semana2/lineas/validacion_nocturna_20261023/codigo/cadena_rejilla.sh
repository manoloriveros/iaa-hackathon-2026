#!/bin/sh
# ROB-C4: rejilla de regularización, semilla 11, versión completa; solo se usa el D² interno del desarrollado para elegir.
set -x
G="timeout 2400 python3 codigo/desarrollado_gbm.py"
for cfg in 'G2:{"num_leaves":7,"min_data_in_leaf":5000,"lambda_l2":100,"feature_fraction":0.7}' 'G3:{"num_leaves":15,"min_data_in_leaf":10000,"lambda_l2":50,"feature_fraction":0.6}' 'G4:{"num_leaves":31,"min_data_in_leaf":3000,"lambda_l2":50,"feature_fraction":0.7}' 'G5:{"num_leaves":15,"min_data_in_leaf":3000,"lambda_l2":200,"feature_fraction":0.5}'; do
  nm=${cfg%%:*}; pj=${cfg#*:}
  $G motor --sufijo _rej${nm}s11 --lr 0.02 --pat 400 --sin make_model --f1 --seed 11 --params "$pj"
  for l in contents buildings; do $G $l --sufijo _rej${nm}s11 --lr 0.02 --pat 400 --f1 --seed 11 --params "$pj"; done
done
echo CADENA_TERMINADA
