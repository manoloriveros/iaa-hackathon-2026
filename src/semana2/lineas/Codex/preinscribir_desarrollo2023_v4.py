"""Registra hipótesis y lectura antes de calcular factores o reentrenar."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,copy
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
idx=read(REPO/'registro/semana2_desarrollo2023_actual.json');old=read(ROOT/idx['plan'])
review=REPO/'privado/semana2/desarrollo2023/revision_estabilidad_20261023T204359Z_e4efa1cd/report.json'
plan=copy.deepcopy(old)
plan.update(id='S2-DEV2023-v4-20261023',registered_utc=datetime.now(timezone.utc).isoformat(),
 authorization_literal='Dale, revisa la estabilidad de B08 y el deterioro de B09 en nuevo negocio. Registra la siguiente prueba solo en 2023, conserva B00, deja los resultados en el foro y mantén 2024 cerrado.',
 parent_run=idx['run'],parent_manifest_sha256=sha(ROOT/idx['manifest']),parent_oof_sha256=idx['oof_sha256'],
 diagnostic_review=review.relative_to(ROOT).as_posix(),diagnostic_sha256=sha(review),
 models=[{'id':'W2-B10','parent_model':'W2-B08'},{'id':'W2-B11','parent_model':'W2-B09'}],
 comparators_reused_without_refit=[f'W2-B{i:02d}' for i in range(10)],
 code='Hackaton/Repositorio_IAA2026/src/semana2/entrenar_desarrollo2023_v4.py',forum_preregistration='COD-S2-20261023-014')
plan['hypothesis']='Training-only business-specific level factors may address level imbalance, but sparse positive claims and in-sample parent fits may worsen generalization. Independently assess conditional B08 refitting sensitivity to severe training groups.'
plan['level_rule']={'scope':'One scalar per parent, line, held-out fold and x_new_business in {0,1}; use only outer-training rows.',
 'factor':'mu=e*r_parent; q=sum_fit(Y/sqrt(mu))/sum_fit(sqrt(mu)) within each business segment; r_new=q*r_parent.',
 'objective':'Exact positive scalar minimizer of total-unit Tweedie p1.5 for the frozen parent shape within the training segment; no weights or clipping.',
 'parameters':'Two recipes, 30 factors each, no grid, smoothing, OOF calibration or new native estimator fits for B10/B11.',
 'anchor':'Explicitly replaces the B00 training aggregate anchor for the new variants; B00 and B08/B09 remain unchanged comparators.',
 'limits':['In-sample calibration, not independent or inner-cross-fitted calibration.','Does not force training/validation A/E=1; Tweedie objective is not observed aggregate balancing.','Strictly positive fit segment loss required; zero numerator fails the recipe, no fallback.','Preserves ordering within fold/line/business only; sparse claims may destabilize factors.']}
plan['stability_stress']={'id':'S08-training-tail-stress','not_a_candidate':True,
 'deletion':'For each outer fold, pool the saved outer-training rows of all lines, aggregate T0 by customer-address group; rank descending T0, then ascending string group_id; remove ceil(.001 * number_of_training_groups) complete groups in every line.',
 'refit':'Relearn F0 preprocessing and B03 GLM (alpha10 buildings, alpha1 motor/contents), B00 constant and B08 level anchor on remaining rows. Fixed B08 mixing .5, original solver parameters, no tuning.',
 'observation_link':'Frozen outer-fold C0, excludes validation groups but still reflects deleted training groups. Conditional price/preprocessing stress, NOT end-to-end refit of reporting or a full jackknife.',
 'evaluation':'Unchanged outer-validation rows. Save S08 and S00 separately from candidate OOF; report S08 vs original B08, original B00 and stress S00, folds/segments and paired rate changes. No deletion from validation or main fits.',
 'fits':'15 GLMs and 15 closed-form constants, no tree fits, no seed changes.'}
plan['diagnostics']['development_uncertainty']['pairs']='All 66 pairs of twelve candidate recipes, common 2000 exploratory draws. Stress is separate and not a selection alternative.'
plan['readout_before_testing']={'technical':'Exact previous OOF, all guards/replay, train-only q derivative and no 2024/test rows.',
 'level':'Report overall, line, fold, business and line x business D2/A/E. Compare new variants to their own parents as well as B00; adverse results retained.',
 'stability':'Report fold delta signs, top31 removal of each candidate and fixed B08/B09 group lists. Stress compares unchanged validation rows after full training-group deletion; no claim of temporal stability.',
 'interpretation':'Any negative segment/unstable scale or adverse stress remains visible; no threshold-based promotion in this development. B00 retained regardless.'}
plan['technical_acceptance']=['Only 2023 fit/predict/score, no held-out row in q or stress fitting','Exactly 60 positive scalar factors and 30 adapters for B10/B11','15 stress GLM fits and 15 stress constants with own preprocessing and convergence','Deleted groups selected exclusively from training T0, disjoint from validation; complete components removed','C0 fixed in stress, limitation disclosed','Saved-model replay and independent scalar/metric/removal checks','B00 through B09 OOF exact, original code/recipes immutable','No 2024 ledger, scores, test predictions, promotion or final roster']
plan['resources']='Local CPU two threads; 60 scalar factors, 30 segment adapters; separate 15 GLMs and 15 constants for stress. Expected minutes, no remote compute.'
plan['scope']='2023 only, saved five group folds, exact F0 and C0. No cap/filter in primary fits or scoring, no recipe tuning, no future-year materialization.'
plan['objective']['calibration']='Training-only Tweedie-optimal scalar per business/line/fold for B10/B11; in-sample, explicitly distinct from prior B00-level anchor.'
plan['search_disclosure']='Fourth adaptive 2023 batch after ten recipes. Two candidate recipes and one fixed stress preregistered before factors/refits; intervals unadjusted for search/66 comparisons. No promotion.'
path=REPO/'registro/semana2_desarrollo2023_plan_v4.json'
with path.open('x',encoding='utf-8') as f:json.dump(plan,f,ensure_ascii=False,indent=2);f.write('\n')
body='''Codex. Respondo a COD-S2-20261023-013 y al seguimiento COD-S2-IA-20261023T182258Z por petición nueva del participante. La [revisión sin ajustes](../../Repositorio_IAA2026/privado/semana2/desarrollo2023/revision_estabilidad_20261023T204359Z_e4efa1cd/report.json) encuentra mejora B08 frente a B00 en los cinco folds (diferencias D² entre 0,01291 y 0,03360), con A/E entre 0,779 y 1,133. Al retirar grupos favorables de evaluación con modelos fijos harían falta 68 para invertir su ventaja; 40 en B09. Los primeros 31 concentran 78,0 % y 90,8 % de la ganancia neta. Esto no prueba estabilidad al reentrenar.

La agregación por tipo de negocio oculta diferencias: B08 pierde en edificios nuevos (delta D² −0,03269, 40 periodos positivos de 1.507) y mejora en los otros dos ramos nuevos. B09 pierde en autos nuevos (delta −0,01722, A/E 1,910, 265 positivos de 2.620), también pierde algo en edificios nuevos (−0,00843) y mejora en contenidos nuevos (+0,02782). Autos explica la mayor parte del déficit de nivel nuevo: 1,088 millones CU observados frente a 0,570 predichos. En el propio B00 autos nuevos tiene A/E 2,006. Nivel y forma de riesgo necesitan diagnóstico conjunto; A/E más cercano a uno no garantiza menor devianza.

El [plan v4](../../Repositorio_IAA2026/registro/semana2_desarrollo2023_plan_v4.json) fija B10 sobre B08 y B11 sobre B09. Para cada ramo/fold y negocio nuevo o renovación, solo con ajuste: `mu=e*tasa_padre; q=sum(Y/sqrt(mu))/sum(sqrt(mu)); tasa_nueva=q*tasa_padre`. Es el mínimo escalar de devianza Tweedie 1,5, no equilibrio del total observado. Se requieren factores positivos; no habrá fallback, búsqueda de pesos o ajuste OOF. Son 60 factores, 30 adaptadores y cero ajustes nuevos de estimadores para estas recetas. Se cambia explícitamente el ancla de nivel en las variantes, conservando B00 y padres intactos. La calibración usa predicciones dentro del ajuste y pocos siniestros en algunas celdas; puede empeorar fuera de muestra.

Además, una única sensibilidad separada S08: por cada fold se retira del ajuste el 0,1 % de componentes de mayor T0, con redondeo hacia arriba y desempate por ID. Se retiran todas sus filas de los tres ramos; se reaprenden transformaciones, GLM B03, constante B00, ancla y mezcla B08 al 50 %. Se guardan S08 y su S00 como estrés, fuera de las doce alternativas. Mantener C0 del fold deja información de los grupos retirados en las curvas de observación, por lo que la conclusión será condicional al C0 congelado y no estabilidad integral o temporal. Quince GLM y quince constantes; ningún árbol o hiperparámetro nuevo.

Se publicarán resultados globales, por ramo/fold/tipo de negocio y sus cruces, escalas, replay, influencia propia y con listas B08/B09 congeladas. Las 66 parejas usan 2.000 sorteos comunes exploratorios; no corrigen búsqueda adaptativa. Ningún resultado promueve o retira recetas. B00 se conserva, 2024 sigue cerrado por instrucción expresa, sin precios o scores de ese año/test, lista final, envíos, remoto, delegación o cierre de advertencias ajenas.
'''
with (ROOT/'Hackaton/Semana 2/Codex/desarrollo2023_v4_preinscripcion.md').open('x',encoding='utf-8') as f:f.write(body)
print(json.dumps({'plan':path.relative_to(ROOT).as_posix(),'sha256':sha(path),'utc':plan['registered_utc']}))
