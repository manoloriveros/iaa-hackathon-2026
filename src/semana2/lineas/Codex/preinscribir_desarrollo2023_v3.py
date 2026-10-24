"""Prueba previa de ancla de nivel y contracción fija; ningún factor calculado."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parent=REPO/'privado/semana2/desarrollo2023/dev2_20261023T180127Z_46d18106'
v1=REPO/'privado/semana2/desarrollo2023/dev_20261023T173828Z_7efe46fc'
review=REPO/'privado/semana2/desarrollo2023/revision_nivel_20261023T181136Z_82668c37/report.json'
old=read(parent/'plan_snapshot.json');diagnostics=copy.deepcopy(old['diagnostics'])
diagnostics['development_uncertainty']['pairs']='All 45 pairs of ten recipes; common 2000 exploratory component draws, no multiplicity or search correction'
diagnostics['no_selection']='Keep B00 and every alternative; no promotion, retirement, equivalence or final confirmation roster here.'
models=[{'id':'W2-B06','parent_model':'W2-B03','shape_weight':1.},
        {'id':'W2-B07','parent_model':'W2-B05','shape_weight':1.},
        {'id':'W2-B08','parent_model':'W2-B03','shape_weight':.5},
        {'id':'W2-B09','parent_model':'W2-B05','shape_weight':.5}]
plan={'id':'S2-DEV2023-v3-20261023','author':'Codex','registered_utc':datetime.now(timezone.utc).isoformat(),
 'authorization_literal':'Dale, revisa el nivel agregado y la influencia de pocos grupos en B03 y B05. Registra la siguiente prueba solo en 2023, conserva B00, deja los resultados en el foro y mantén 2024 cerrado.',
 'parent_run':str(parent.relative_to(ROOT)).replace('\\','/'),'reference_model_run':str(v1.relative_to(ROOT)).replace('\\','/'),
 'parent_manifest_sha256':sha(parent/'manifest.json'),'parent_oof_sha256':sha(parent/'oof_2023.parquet'),
 'diagnostic_review':str(review.relative_to(ROOT)).replace('\\','/'),'diagnostic_sha256':sha(review),
 'selection_policy':old['selection_policy'],'selection_policy_sha256':old['selection_policy_sha256'],
 'objective':old['objective'],'observation_link':old['observation_link'],'features':old['features'],
 'models':models,'comparators_reused_without_refit':['W2-B00','W2-B01','W2-B02','W2-B03','W2-B04','W2-B05'],
 'level_rule':{'scope':'For each parent, line and outer fold, use exactly the saved outer-training rows and corresponding frozen C0 exposure. No held-out labels/features/distribution for fitting the factor.',
   'factor':'s = sum_fit(e * c0) / sum_fit(e * r_parent); c0 is the saved B00 annual constant for the same fold/line',
   'prediction':'r_new = (1-w)*c0 + w*s*r_parent; observed prediction = e*C0_adjusted_rate, w in {1,0.5} fixed above',
   'anchor':'B00 fitted-model level, not observed sum(Y), not OOF totals and not a private/public score',
   'shared_factors':'Two parents * three lines * five folds = 30 positive factors, each shared between weights 1 and .5',
   'moment':'For every outer-training fold/line, sum(e*r_new)=sum(e*c0). This is a training moment only; no held-out equality or A/E=1 guarantee.',
   'limits':['Uses fitted in-sample risk predictions for normalization; not independent or inner-OOF calibration',
             'B00 anchor itself depends on training claims and may be influenced by severe events',
             'Positive scaling and fixed mixing preserve within-fold/line annual-rate ordering; this does not prove sound risk shape or ultimate level']},
 'diagnostics':diagnostics,
 'readout_before_testing':{'level':'First check exact fit moment and unchanged comparators; then report whether held-out totals move closer to B00 and observed A/E, by line/fold and business. No forcing held-out totals.',
   'influence':'Recompute each new-vs-B00 top31 removal and bootstrap. Also remove the frozen top31 favorable groups from its parent review, using the identical set across parent/anchored/shrunk variants. No removal in fit, primary score or level factor.',
   'contraction':'With w=.5, annual-rate deviation from B00 is exactly half that of the anchored parent in each fit scope. Check whether evaluation influence is reduced; no guarantee of half deviance contribution.',
   'uncertainty':'All point/interval/scenario/segment results remain exploratory after adaptive 2023 search. Retain B00 regardless of this batch readout.'},
 'technical_acceptance':['Only 2023 materialized and supplied to fit-factor/predict/score','Exact parent-model, target, fold, C0 and F0 hashes',
   'Factor rejects held-out training rows, invalid exposure/rates, or another year','30 training-only factors and 60 adapter bundles; zero new GLM/tree fits',
   'Exact training aggregate anchor and fixed w=.5 contraction','No held-out outcomes used for scales or weights',
   'Scales/models/OOF replay with base fit functions blocked; independent scale and metric reconstruction',
   'All six previous OOF tables including B00 unchanged','No 2024/test prices, scores, ledger opening or final confirmation roster'],
 'scope':'Local only, same 2023 five customer-address folds; no row trimming, cap, extra weights, seeds, optimization of mixing, new features, prices or test predictions.',
 'resources':'CPU, two threads; reuse 60 parent/reference bundles to learn 30 scalar factors, save 60 new adapters, reuse six OOF comparators. Expected minutes, no base-estimator retraining or remote compute.',
 'search_disclosure':'Motivated by all earlier 2023 results; four recipes fixed before their factors/predictions. No tuning on this batch; intervals do not correct adaptive search or 45 pairwise comparisons.',
 'code':'Hackaton/Repositorio_IAA2026/src/semana2/entrenar_desarrollo2023_v3.py',
 'forum_preregistration':'COD-S2-20261023-012','reference_retained':'W2-B00','confirmation_2024_open':False,'promotion':False,'final_confirmation_roster_frozen':False}
# The inherited objective described the preceding batch; make the new explicit component visible.
plan['objective']=copy.deepcopy(plan['objective']);plan['objective']['calibration']='Explicit B00 training-level anchor and fixed contraction, exactly as level_rule; no held-out or public calibration'
path=REPO/'registro/semana2_desarrollo2023_plan_v3.json'
with path.open('x',encoding='utf-8') as f:json.dump(plan,f,ensure_ascii=False,indent=2);f.write('\n')
body='''Codex. Continúo COD-S2-20261023-011 por nueva petición del participante. La [revisión de nivel e influencia](../../Repositorio_IAA2026/privado/semana2/desarrollo2023/revision_nivel_20261023T181136Z_82668c37/report.json) usa solo OOF2023 congelado y no calculó factores o nuevas predicciones.

B03 predice 14,320 millones CU y B05 14,113 frente a 15,614 de B00 y 15,297 observados. El déficit respecto del observado se concentra en edificios: 0,718 millones CU en B03 y 0,695 en B05. Los 31 grupos más favorables representan 140,5 % y 130,0 % de la ventaja neta, respectivamente; compensan contribuciones adversas del resto. Contienen 12,31 % y 9,48 % del coste observado, con cerca de 0,12 %/0,13 % de la exposición. Basta retirar 14 grupos favorables en B03 o 18 en B05 para invertir la ventaja. Diecinueve grupos pertenecen a ambas listas. Son diagnósticos condicionales con modelos fijos, no errores de datos ni un jackknife con reentrenamiento.

El [plan v3](../../Repositorio_IAA2026/registro/semana2_desarrollo2023_plan_v3.json) fija una prueba de nivel y contracción antes de calcular resultados. Para cada padre, ramo y fold se aprende exclusivamente en sus filas de ajuste:

`s = sum_ajuste(e × c0) / sum_ajuste(e × r_padre)`

Aquí c0 es la tasa B00 ya guardada y e su exposición efectiva C0. No se usa la suma observada para forzar A/E, el total OOF ni información del fold retenido para aprender s. Se comprueba la igualdad del total predicho de ajuste con el de B00. Usa predicciones dentro del ajuste, no una calibración independiente o interna fuera de muestra; el ancla B00 también depende de siniestros y puede ser sensible a eventos grandes.

- B06: forma B03 × s, sin cambiar su orden anual de riesgos dentro del ramo/fold.
- B07: forma B05 × s, con la misma regla.
- B08: 50 % de la tasa B00 y 50 % de B06.
- B09: 50 % de la tasa B00 y 50 % de B07.

Los pesos 1 y 0,5 quedan fijos; no se buscará el mejor. Las cuatro recetas comparten treinta factores y se guardarán sesenta adaptadores, sin ajustar nuevos GLM o árboles. B08/B09 reducen exactamente a la mitad la desviación de la tasa anclada frente a B00, pero eso no garantiza reducir a la mitad su influencia en devianza. No se elimina ningún grupo de ajuste, calibración o score completo.

La lectura previa exige comprobar el momento de ajuste y después observar nivel OOF por ramo/fold, A/E, devianza e influencia. Se repetirá el retiro de 31 grupos favorables de cada receta y, además, el de la lista congelada de su padre para hacer comparable el diagnóstico. Se conservarán B00–B05 exactos, las 45 parejas de diez recetas y 2.000 sorteos comunes exploratorios. La búsqueda adaptativa y multiplicidad quedan declaradas; no se confunden con confirmación de2024 o equivalencia.

Se mantiene B00 cualquiera que sea el punto de esta tanda; todas las alternativas siguen registradas. Los supuestos del último y los bloqueos de recetas anteriores conservan sus responsables. Se recibió el cierre técnico del vínculo del selector y el seguimiento GOV005 publicados por otros encargos, sin adjudicar cierres aquí. 2024 permanece cerrado por instrucción expresa, sin importar su avance. No hay lista final congelada, precios de2024/test, envíos, remoto o delegación en esta prueba.
'''
with (ROOT/'Hackaton/Semana 2/Codex/desarrollo2023_v3_preinscripcion.md').open('x',encoding='utf-8') as f:f.write(body)
print(json.dumps({'plan':str(path.relative_to(ROOT)),'sha256':sha(path),'recipes':[x['id'] for x in models],'new_base_estimator_fits':0,'training_level_factors':30,'confirmation_2024_open':False}))
