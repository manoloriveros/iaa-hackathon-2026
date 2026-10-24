"""Fija tres recetas tras revisar v1; no prueba prefijos ni ajusta estimadores."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parent=REPO/'privado/semana2/desarrollo2023/dev_20261023T173828Z_7efe46fc'
review=REPO/'privado/semana2/desarrollo2023/revision_20261023T175646Z_4924665e'
old=read(parent/'plan_snapshot.json');glm=copy.deepcopy(old['models'][1]);boost=copy.deepcopy(old['models'][2])
glm.update(id='W2-B03',routing={'buildings':'new_fit','motor':'reuse_W2-B01','contents':'reuse_W2-B01'})
glm['params']['alpha']=10.
glm['hypothesis']='Stronger ridge in buildings reduces coefficient variance and improves buildings OOF relative to B01; other lines unchanged. No trimming, capital change or intercept recalibration.'
boost.update(id='W2-B05')
boost['params'].update(n_estimators=80,num_leaves=2,max_depth=1,min_child_samples=1000,reg_lambda=100.)
boost['hypothesis']='Joint capacity/regularization reduction narrows the generalization gap relative to B02; individual parameter causality is not identified.'
boost['stopping']='Fixed 80 rounds, no validation set, early stopping or parameter search'
prefix={'id':'W2-B04','family':'LGBMBoosterPrefix','parent_model':'W2-B02','prefix_trees':25,
        'recipe':'Save exactly the first 25 trees from each frozen B02 fold model; identical data, categories, weights and tree path; no further training or stage search.',
        'hypothesis':'A fixed shorter path reduces the 300-tree generalization gap; 25 is declared before any prefix metric is computed, not chosen from a scored curve.'}
diagnostics=copy.deepcopy(old['diagnostics'])
diagnostics['development_uncertainty']['pairs']='All fifteen pairs of six recipes, shared draws; exploratory without multiplicity/selection correction'
diagnostics['no_selection']='Retain all six recipes and artifacts; no promotion, retirement, equivalence or final confirmation roster frozen in this batch.'
acceptance=[x.replace('2024 ledger remains unopened and selector finding remains open','2024 remains unopened even if a separate task repairs the selector') for x in old['technical_acceptance']]
plan={'id':'S2-DEV2023-v2-20261023','author':'Codex','registered_utc':datetime.now(timezone.utc).isoformat(),
 'authorization_literal':'Dale, revisa el GLM en edificios y la brecha de LightGBM entre ajuste y validación. Registra las recetas antes de probar otra tanda solo en 2023, conserva la referencia y deja los resultados en el foro. Mantén 2024 cerrado.',
 'parent_run':str(parent.relative_to(ROOT)).replace('\\','/'),'parent_manifest_sha256':sha(parent/'manifest.json'),
 'parent_oof_sha256':sha(parent/'oof_2023.parquet'),'parent_recipe_sha256':sha(parent/'plan_snapshot.json'),
 'diagnostic_review':str((review/'report.json').relative_to(ROOT)).replace('\\','/'),'diagnostic_sha256':sha(review/'report.json'),
 'selection_policy':old['selection_policy'],'selection_policy_sha256':old['selection_policy_sha256'],
 'objective':old['objective'],'observation_link':old['observation_link'],'features':old['features'],
 'models':[glm,prefix,boost],'comparators_reused_without_refit':['W2-B00','W2-B01','W2-B02'],
 'readout_before_testing':{'B03':'Buildings OOF D2 improvement and reduced train-vs-OOF gap relative to B01, other-line predictions identical',
                         'B04':'Global OOF improvement and smaller generalization gap relative to B02; all lines/folds reported',
                         'B05':'Global OOF improvement and smaller generalization gap relative to B02; aggregate level and subgroup risks reported',
                         'all':'Also compare each against unchanged B00. No point score or exploratory interval promotes, retires or declares equivalence.'},
 'diagnostics':diagnostics,'technical_acceptance':acceptance,
 'scope':'Only 2023 frozen inputs and five persisted customer-address folds. No new split, label trimming, weather, target calibration, blends, extra seeds, scans or 2024/test predictions/scores.',
 'resources':'Local CPU, two threads, 20 new estimator fits (5 buildings GLM + 15 shallow boosting), 10 GLM bundle reuses, 15 prefix extractions, three comparator OOF tables reused. Expected minutes; no remote compute.',
 'technical_controls_extra':['B00/B01/B02 OOF floats unchanged','B03 other-line bundles/predictions unchanged from B01','B04 exactly 25 parent trees and identical categories/outputs to parent num_iteration=25','All coefficients, encoders and category lists from training rows only','Saved-model replay with fit disabled','Original v1 source and artifacts remain unchanged'],
 'search_disclosure':'This batch is adaptively motivated by 2023 v1 results and diagnostic review. Exploratory CV intervals do not correct this prior selection or all fifteen six-model comparisons.',
 'reference_retained':'W2-B00','all_alternatives_preserved':['W2-B01','W2-B02','W2-B03','W2-B04','W2-B05'],
 'code':'Hackaton/Repositorio_IAA2026/src/semana2/entrenar_desarrollo2023_v2.py',
 'forum_preregistration':'COD-S2-20261023-010','confirmation_2024_open':False,'promotion':False,'final_confirmation_roster_frozen':False}
path=REPO/'registro/semana2_desarrollo2023_plan_v2.json'
with path.open('x',encoding='utf-8') as f:json.dump(plan,f,ensure_ascii=False,indent=2);f.write('\n')
body='''Codex. Continúo COD-S2-20261023-009 por la nueva petición del participante. Antes de probar otra tanda revisé los modelos y OOF guardados, con fit bloqueado y solo 2023. La [revisión](../../Repositorio_IAA2026/privado/semana2/desarrollo2023/revision_20261023T175646Z_4924665e/report.json) conserva código y detalle.

En edificios, el GLM gana en las 12.083 filas sin coste y pierde en las 497 positivas; cinco grupos adversos bastan para cambiar el signo al retirarlos solo como diagnóstico. No se retiran de la pérdida o del entrenamiento. Los 26 capitales desconocidos no tienen siniestros y explican una contribución pequeña al deterioro; no justifican corregir capitales. Algunos coeficientes categóricos cambian de signo entre folds. En el árbol 300 de LightGBM hay hojas con pocos positivos, incluso ninguno en contenidos. Es evidencia de soporte débil, no prueba causal de un parámetro.

Precisión a la redacción anterior: min_child_samples=200 es el parámetro declarado, no una garantía de doscientas filas reales por hoja; LightGBM lo aproxima mediante Hessianos. La revisión encontró hojas más pequeñas, coherentes con la [documentación oficial](https://lightgbm.readthedocs.io/en/v4.6.0/Parameters.html#min_data_in_leaf). No se cambió la receta v1.

El [plan v2](../../Repositorio_IAA2026/registro/semana2_desarrollo2023_plan_v2.json) fija tres recetas nuevas antes de sus resultados:

- W2-B03: el mismo GLM de edificios con alpha=10; autos y contenidos reutilizan exactamente B01. Cambia solo la penalización de edificios.
- W2-B04: exactamente los primeros 25 árboles de cada modelo B02 guardado. No se entrenan de nuevo ni se puntuó antes otro prefijo; 25 queda fijado ahora, sin elegir el mejor punto de una curva.
- W2-B05: LightGBM con 80 rondas, árboles de profundidad uno y dos hojas, min_child_samples=1000 y L2=100; el resto coincide con B02. Es una reducción conjunta de capacidad y no aísla cada parámetro.

Se mantienen F0, T0/C0, peso sqrt(e), particiones y semilla. No se cambia nivel ni se añaden mezclas. Habrá veinte ajustes nuevos, diez reutilizaciones GLM y quince extracciones de prefijo, con CPU local y dos hilos. Se comparan las seis recetas contando v1, con todos los puntos, segmentos, brechas, influencia y 2.000 remuestreos exploratorios comunes. La búsqueda ya informada por v1 se declara; los intervalos no corrigen esa selección ni las quince parejas.

La lectura previa exige comprobar si B03 mejora edificios y si B04/B05 reducen la brecha y el deterioro frente a B02; cada alternativa también se contrasta con B00 sin cambios. No se cambiará una receta después de ver esta tanda. Se conserva la referencia y toda alternativa, con resultados adversos. La aceptación técnica incluye replay, parámetros, encoders dentro de fold, prefijo exacto y comparadores inalterados.

2024 permanece cerrado por instrucción expresa del participante, aunque otro encargo avance la corrección del selector. No hay promoción ni lista final congelada, scores 2024, test, envíos o entrenamiento remoto en este plan. El bloqueo previo de B02 y su alias S2-VAL-MOD-007 no se dan por cerrados por registrar recetas diferentes.
'''
with (ROOT/'Hackaton/Semana 2/Codex/desarrollo2023_v2_preinscripcion.md').open('x',encoding='utf-8') as f:f.write(body)
print(json.dumps({'plan':str(path.relative_to(ROOT)),'sha256':sha(path),'new_fits':20,'reference':'W2-B00','confirmation_2024_open':False}))
