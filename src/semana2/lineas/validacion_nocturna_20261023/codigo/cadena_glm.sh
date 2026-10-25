#!/bin/sh
set -x
for l in motor buildings contents; do
  timeout 2400 python3 codigo/desarrollado_glm.py $l 1 --f1 --sufijo f1
  timeout 2400 python3 codigo/desarrollado_glm.py $l 1 --f1 --años 2021,2022,2023 --conf --sufijo f1conf
done
echo CADENA_TERMINADA
