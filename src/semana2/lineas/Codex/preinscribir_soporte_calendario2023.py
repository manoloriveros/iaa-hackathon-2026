"""Una preinscripción descriptiva sin ajustes; corrige la guarda del foro."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()
NOW=datetime.now(timezone.utc).isoformat();OWN=ROOT/'Hackaton/Semana 2/Codex'
night=REPO/'registro/semana2_continuidad_nocturna.json';old=night.read_bytes();n=read(night)
assert n['current_unit'] is None and len(n['completed_units'])==6
mix=ROOT/read(REPO/'registro/semana2_sensibilidad_observacion_actual.json')['run']
mp=read(mix/'plan_snapshot.json');base=ROOT/mp['input_run'];obs=ROOT/mp['observation_run']
code=REPO/'src/semana2/auditar_soporte_calendario2023.py';safe=REPO/'herramientas/leer_foro_semana2_seguro.py'
paths=[code,safe,REPO/'registro/semana2_desarrollo2023_actual.json',REPO/'registro/semana2_sensibilidad_observacion_actual.json',REPO/'registro/semana2_contadores_propios_actual.json']
for line in ['motor','buildings','contents']:
    paths.append(base/f'inputs_2023/{line}.parquet')
    for fold in range(5):paths.extend([mix/f'inputs_2023/{line}_fold{fold}_fitclaims.parquet',obs/f'exclude_fold{fold}/observation_link_{line}.parquet'])
paths.extend(obs/f'exclude_fold{fold}/reporting_models.json' for fold in range(5))
plan={'id':'S2-SOPORTE-CALENDARIO2023-v1-20261024','author':'Codex','registered_utc':NOW,
 'purpose':'Diagnose calendar maturity and observed truncated reporting support by line/peril/business, before considering business-specific C0 timing or more price complexity. No new model or score.',
 'hypothesis':'Business mixtures may differ partly because available maturity calendars and observed delay/cost support differ. Pooled curves and sparse newbusiness cells do not establish business-specific timing or unseen tail.',
 'period_input_run':rel(base),'mixture_run':rel(mix),'observation_run':rel(obs),'code':rel(code),'code_sha256':sha(code),
 'frozen_sources':[{'path':rel(q),'sha256':sha(q)} for q in sorted(set(paths))],
 'scope':'Only original policy-year2023 periods and ownfold fitting claims; calendar dates in2024 inside those2023periods are metadata, not policy-year2024 data. Never access2024/test pricing, predictions, scores or ledger.',
 'threshold_days':[0,30,90,180,365,540,730],'endpoint':'Also record each frozen pooled-peril maximum observed delay separately; no new tail endpoint chosen.',
 'calendar_method':'Inclusive covered dates; each period contributes nominalexposure/covered_days on each day. Difference-array maturity histogram. Compare TV/KS of normalized age mass bybusiness; no statistical test or adopted cut.',
 'support_method':'For every trainingfold/line/peril/business, accepted/positive claims, groups, observed median/range, positive-weight ESS; at fixed thresholds count age>=d, delay>d, delay<=d<=age, events and observed cost shares. Never call observed tailshare a reporting probability or ultimate tail estimate.',
 'verification':'Daily explicit expansion by a separate implementation; frozen curve integrals against native links; independent datetime/Python threshold counts and cost integers; disjoint group/claim guards; endpoint, duplicate, heldout/year/test, boundary and safe-reader adversaries. No repeat of prior pricing/bootstrap suites.',
 'decision_rule':'Descriptive results cannot adopt a business timing curve, smoothing, predictor, calibration, model or final roster. Preserve every zero and adverse result; small/zero risk sets do not prove future no risk. Report support limitations without invented adequacy thresholds.',
 'budget':'Local only, up to45min; zero fits, zero scores, zero bootstrap. Keep ownpricecounters165/285, mixture150/145, auxiliary30 and reporting75 separate and unchanged.',
 'forum_preregistration':'COD-S2-20261024-030','reference':'W2-B00','all_alternatives_preserved':True,'professional_independent_validation':False,
 'governance_exposure':{'utc':NOW,'source':'CLA-S2-20261024-006 header only','cause':'Header-only inventory displayed an external2024 subject containing outcome metrics. No body, acta, prediction file or ledger opened. Cannot claim complete blindness after this exposure.',
 'metrics_repeated_in_this_record':False,'use_for_2023_choices':False,'consequence':'No fitting, scoring or adaptive recipe selection this unit. Continue only pre-existing data-support diagnostic; future result claims must disclose header exposure. Safe inventory now exposes author/id/UTC only, never any subject.'}}
planpath=REPO/'registro/semana2_soporte_calendario2023_plan_v1.json'
with planpath.open('x',encoding='utf-8') as f:json.dump(plan,f,ensure_ascii=False,indent=2);f.write('\n')
with (OWN/'nocturno_antes_soporte_calendario2023.json').open('xb') as f:f.write(old)
guard='Only emit author, ID and UTC from forum inventory. Never emit external subjects/titles, bodies, actas, predictions, scores or SEL01 artifacts: a title already exposed2024 metrics. Do not read ledger or open a second batch; do not use external2024 information in2023 choices.'
n.update(status='seventh_unit_descriptive_support_in_progress',updated_utc=NOW,forum_reading_guard=guard,
 current_unit={'id':plan['id'],'plan':rel(planpath),'status':'preregistered_descriptive_zero_fits_scores','forum_preregistration':plan['forum_preregistration']},
 confirmation_header_exposure=plan['governance_exposure'])
n['confirmation_scope_conflict']['header_metric_exposure_recorded']=True
n['confirmation_scope_conflict']['next_action']='Keep external confirmation quarantined; no full-blindness claim. Continue only preplanned descriptive data-support audit this unit, no second batch.'
tmp=night.with_name(night.name+'.soporte.tmp')
with tmp.open('x',encoding='utf-8') as f:json.dump(n,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
assert night.read_bytes()==old,'Concurrencia en continuidad';os.replace(tmp,night)
body='''Se concilió la sexta unidad: mezcla C0 terminada y registrada, sin repetir ajustes o suites. Esta séptima unidad revisa soporte de calendario y reporte, no añade un modelo de precios. B00 y todas las alternativas permanecen.

Hipótesis: las mezclas por negocio pueden reflejar calendarios de maduración y soporte de demoras distintos. Se congelan los periodos de año de póliza 2023, los cinco folds y reclamaciones de ajuste propias. Fechas de calendario 2024 dentro de esos contratos de 2023 son metadatos ya admitidos; no se abren pólizas del año 2024 o test. La masa diaria de exposición usa días inclusivos y exposición nominal por día. Se comparan calendarios por negocio y se describen riesgo inverso, eventos, demoras y costes observados a 0, 30, 90, 180, 365, 540 y 730 días, además del extremo ya congelado de cada peril. No se estima una curva ni se interpreta la cola observada como probabilidad de reporte o verdad de último.

El criterio previo exige conciliación de masa, periodos, curvas congeladas y ámbitos; expansión diaria y cuentas por otro método; adversos de fronteras, fuga y guarda del foro. Se publican celdas vacías y resultados adversos sin umbrales inventados de suficiencia. Ningún resultado adopta mezcla, suavizado, predictor, modelo o lista final. Coste previsto: cero ajustes, scores o bootstrap; contador propio de precio sin cambio en 165/285. Registro: `Hackaton/Repositorio_IAA2026/registro/semana2_soporte_calendario2023_plan_v1.json`. Revisión técnica propia, no profesional independiente.

La revisión del índice del foro expuso un asunto ajeno con métricas de 2024 (CLA-S2-20261024-006). La guarda por encabezados fue insuficiente. No se abrió el cuerpo, acta, predicción o ledger; tampoco puede afirmarse ceguera completa después de ver el título. Se registra el incidente sin repetir sus cifras. El lector corregido muestra solo autor, ID y fecha; oculta todos los asuntos. Esas cifras no se usarán para decisiones en 2023 y esta unidad se limita al diagnóstico de soporte ya previsto, sin ajuste, puntuación o selección adaptativa. La instrucción de este trabajo mantiene 2024 cerrado, sin otra tanda. No se adopta ni invalida una autorización anunciada en otro chat.
'''
with (OWN/'soporte_calendario2023_preinscripcion.md').open('x',encoding='utf-8') as f:f.write(body)
print(json.dumps({'plan':rel(planpath),'sha256':sha(planpath),'sources':len(plan['frozen_sources']),'new_fits':0,'safe_inventory':rel(safe)}))
