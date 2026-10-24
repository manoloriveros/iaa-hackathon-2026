"""Diagnóstico sin ajuste, corte inmutable frente a concurrencia."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,os
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026';OWN=ROOT/'Hackaton/Semana 2/Codex'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()
NOW=datetime.now(timezone.utc).isoformat();night=REPO/'registro/semana2_continuidad_nocturna.json';before=night.read_bytes();n=read(night)
assert 'S2-B19-ESTABILIDAD2023-v1-20261024' not in [x['id'] for x in n['completed_units']]
mode='current_unit' if n.get('current_unit') is None else 'parallel_artifact_diagnostic'
run=REPO/'privado/semana2/desarrollo2023/dev8_20261024T013001Z_e8a35214';vp=read(run/'plan_snapshot.json');base=ROOT/vp['input_run'];code=REPO/'src/semana2/diagnosticar_estabilidad_b19_2023.py'
current=REPO/'registro/semana2_desarrollo2023_actual.json';counter=REPO/'registro/semana2_contadores_propios_actual.json'
for source,name in [(current,'catalogo_antes_estabilidad_b19.json'),(counter,'contadores_antes_estabilidad_b19.json'),(night,'nocturno_antes_estabilidad_b19.json')]:
    with (OWN/name).open('xb') as f:f.write(source.read_bytes())
catalogsnapshot=OWN/'catalogo_antes_estabilidad_b19.json';countersnapshot=OWN/'contadores_antes_estabilidad_b19.json'
claims=REPO/'privado/semana2/desarrollo2023/mezcla_20261024T004833Z_e8ff18e0/inputs_2023/claims_2023.parquet'
paths=[code,run/'plan_snapshot.json',run/'report.json',run/'oof_2023.parquet',run/'verification.json',run/'fixture_checks.json',claims,catalogsnapshot,countersnapshot]
for line in ['motor','buildings','contents']:
    for fold in range(5):
        paths.extend([run/f'models/W2-B19_{line}_fold{fold}/bundle.joblib',base/f'models/W2-B14_{line}_fold{fold}/bundle.joblib'])
        if line in ['motor','buildings']:paths.append(run/f'inputs_2023/{line}_fold{fold}.parquet')
p={'id':'S2-B19-ESTABILIDAD2023-v1-20261024','author':'Codex','registered_utc':NOW,
 'authorization_literal':'Dale, revisa la estabilidad de los coeficientes y la influencia de grupos en B19, sobre todo en edificios y autos nuevos. Usa los artefactos de 2023 sin reentrenar, conserva B00, deja los resultados en el foro y mantén 2024 cerrado.',
 'hypothesis':'B19 coefficient dispersion may reflect small influential training components, while OOF deterioration may be concentrated in different heldout groups. Separate these mechanisms without refitting or using external outcomes.',
 'b19_run':rel(run),'b14_run':rel(base),'oof':rel(run/'oof_2023.parquet'),'claims_2023':rel(claims),'code':rel(code),'code_sha256':sha(code),
 'catalog_snapshot':rel(catalogsnapshot),'counter_snapshot':rel(countersnapshot),'forum_prior':'COD-S2-20261024-036',
 'continuity_registration_mode':mode,'completed_units_at_start':len(n['completed_units']),
 'concurrent_unit_at_start':n.get('current_unit'),'prior_compound_guard_failure':'An earlier attempt required exactly9completed units. It stopped before creating a plan/body or calculating anything. Dependent append/diagnostic attempts then failed for missing files. Reconciliation found10completedunits; no external model results adopted.',
 'coefficient_comparison':'All15 B19 andB14 savedbundles, original numeric slopes beta_std/scale and intercept centering correction; compare only identical categorical reference coding. No fabricated zero for absent/rare categories. Five overlappingfolds are not independent CI.',
 'focus':['buildings all','motor newbusiness'],'removal_k':[1,5,10,31],
 'OOF_influence':'Group sum A_g=devianceB19-devianceB14. Rank strictlypositive adverse and strictlynegative favorable, break ties bygroup_id, keep at mostk. All single-group evaluation deletions plus fixedk cumulative deletions; recompute common null. Segment deletion is withinsegment; global deletion removes fullcomponents acrossalllines. No physical deletion or model/C0 refit, no new bootstrap or oldglobal31 repetition.',
 'training_local_influence':'Onlymotor/buildings savedfit models. Z native transformeddesign+intercept; y=T0/e,w=sqrt(e)/sum; g_i=w*(sqrtmu-y/sqrtmu), h_i=.5*w*(sqrtmu+y/sqrtmu). H=Z.Tdiag(h)Z. GroupG=sum(g_iZ_i); localdeletiondelta=H^-1G using fullH, not refitted deletion. Report originalscale coverage/newbusiness slopes, traceleverage and solve residuals. No predictions or scores from changedcoefficients.',
 'max_hessian_condition':1e12,'condition_rule':'If Hessian nonpositive or condition>1e12, mark localinfluence notestimable, no pseudoinverse/ridge or silentfix. This is local approximation only and unreliable for large/highleverage components; C0 staysfixed.',
 'verification':'New independent contribution sums/generaldeviance/sklearn deletion checks, rawscale reconstruction, Hessian directionalfinite differences and Cholesky/QR solving by another method, all fit entrypoints blocked. Boundary/tie/zero-null/year/duplicate/heldout adversaries and real flow checks. Do not repeat prior bootstrap or native15fit suite.',
 'limits':['OOF group loss is not training parameter influence; a group never trains its own validationfold model','Group in one validationfold appears in four other fittingviews, not four independent observations','No coefficient or group deletion adopted; all outputs exploratory after adaptive research','Prior external2024 header exposure disclosed; no completeblindness claim or externaloutcome use'],
 'resources':'Local up to45min,0fits/newmodels/bootstrap, ten small Hessian diagnostics only; B00 and all alternatives/source hashes preserved. Current counters snapshot only; preserve concurrentwork and do not overwrite othermodel indices/counters.',
 'reference':'W2-B00','ledger_read':False,'professional_independent_validation':False,
 'frozen_sources':[{'path':rel(x),'sha256':sha(x)} for x in sorted(set(paths))]}
pp=REPO/'registro/semana2_b19_estabilidad2023_plan_v1.json'
with pp.open('x',encoding='utf-8') as f:json.dump(p,f,ensure_ascii=False,indent=2);f.write('\n')
entry={'id':p['id'],'plan':rel(pp),'status':'preregistered_no_refit_or_bootstrap','forum_preregistration':p['forum_prior']}
n['updated_utc']=NOW
if mode=='current_unit':n.update(status='B19_artifact_stability_diagnostic_in_progress',current_unit=entry)
else:n.setdefault('parallel_artifact_diagnostics',{})[p['id']]=entry
tmp=night.with_name(night.name+'.estb19.tmp')
with tmp.open('x',encoding='utf-8') as f:json.dump(n,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
assert night.read_bytes()==before,'Concurrencia';os.replace(tmp,night)
body='''Se registra el diagnóstico de estabilidad e influencia de B19 antes del cálculo, por solicitud directa. Se usan únicamente sus artefactos guardados de 2023, B14 como padre y B00 como referencia conservada. No habrá entrenamiento, receta nueva, bootstrap o cambios de parámetros, T0 o C0. Plan: `Hackaton/Repositorio_IAA2026/registro/semana2_b19_estabilidad2023_plan_v1.json`.

Se comparan los quince modelos por ramo/fold, devolviendo coeficientes numéricos a su escala original y alineando referencias categóricas; cinco folds solapados no dan cinco observaciones independientes. Se separa contribución OOF del grupo de su influencia sobre parámetros de ajuste: cada componente está ausente de su propio modelo retenido.

En edificios y autos nuevos se sumará por componente la diferencia de desviancia B19−B14. Se describen todos los retiros individuales de evaluación y retiros de 1, 5, 10 y 31 grupos adversos o favorables, con empates por ID y sin completar con grupos de signo contrario. Se recalcula la nula común. El diagnóstico de segmento retira solo sus filas; el global retira el componente completo en todos los ramos. Nada se borra de los datos o modelos y no se repite el anterior remuestreo o retiro global de 31.

En los diez ajustes guardados de autos/edificios se calcula una aproximación local estándar del GLM: gradiente por componente y Hessiano observado completo, deltaβ≈H⁻¹G_g. Se reportan efecto de cobertura/nuevo negocio en escala original, leverage, condicionamiento y residuo de solución. No es un modelo reentrenado ni una eliminación exacta; no se predecirá o puntuará con coeficientes alterados. Hessiano no positivo o condición mayor que 1e12 deja ese diagnóstico no estimable, sin ridge o pseudoinversa. Curvas de reporte y capital permanecen congelados.

La verificación separará fórmulas de pérdida, claves y grupos, escala de coeficientes, derivadas por diferencias finitas y soluciones por otro método, con fit bloqueado y adversos focales. Los componentes con costes conocidos se describirán por peril sin publicar IDs privados. Se conservan resultados adversos y la distinción entre causalidad, aproximación local y evaluación OOF. Sin promoción, retiro de alternativas o lista final.

2024 sigue cerrado en este trabajo, también test, actas/predicciones/scores y ledger. Se conserva la exposición previa de un título ajeno, sin repetir o usar cifras ni afirmar ceguera completa. El lector solo muestra autor, ID y fecha; no se adopta una orden de otra conversación. No se toca entrenamiento, índices o contadores de otras líneas concurrentes, ni otras automatizaciones, remoto, envíos, publicaciones o delegación. Revisión propia, no profesional independiente ni aprobación humana.
'''
with (OWN/'estabilidad_b19_2023_preinscripcion.md').open('x',encoding='utf-8') as f:f.write(body)
print(json.dumps({'plan':rel(pp),'sha256':sha(pp),'frozen_sources':len(paths),'new_fits':0}))
