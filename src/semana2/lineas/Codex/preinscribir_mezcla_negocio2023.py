"""Congela la mezcla por peril/negocio sin elegir parámetros por nuevos scores."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,os
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026';FOLDER=ROOT/'Hackaton/Semana 2/Codex'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
def dump(path,obj):
    with path.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
main=REPO/'registro/semana2_desarrollo2023_actual.json';idx=read(main);prior=REPO/'registro/semana2_sensibilidad_observacion_actual.json';oldidx=read(prior);counters=REPO/'registro/semana2_contadores_propios_actual.json';co=read(counters)
assert idx['id']=='S2-DEV2023-v7-20261024' and oldidx['id']=='S2-C0-RESERVAS2023-v1-20261024' and co['cumulative_price_base_fits']==135 and co['cumulative_closed_form_constants']==195
old=read(ROOT/oldidx['plan']);v6=ROOT/old['input_run'];f0=ROOT/old['observation_run'];code=REPO/'src/semana2/sensibilidad_mezcla_negocio2023.py'
for source,name in [(prior,'sensibilidad_antes_mezcla_negocio2023.json'),(counters,'contadores_antes_mezcla_negocio2023.json')]:
    with (FOLDER/name).open('xb') as f:f.write(source.read_bytes())
claim_source=ROOT/oldidx['run']/'inputs_2023/claims_2023.parquet';paths=[main,ROOT/idx['oof'],claim_source,code,REPO/'src/semana2/entrenar_desarrollo2023.py',REPO/'src/semana2/entrenar_desarrollo2023_v5.py',v6/'plan_snapshot.json',ROOT/old['selection_policy'],FOLDER/'sensibilidad_antes_mezcla_negocio2023.json',FOLDER/'contadores_antes_mezcla_negocio2023.json']
for fold in range(5):
    paths += [f0/f'exclude_fold{fold}/reporting_models.json',f0/f'exclude_fold{fold}/severity_fit_weights.parquet']
    for line in ['motor','buildings','contents']:
        paths += [v6/f'inputs_2023/{line}.parquet',v6/f'variant_inputs/{line}_fold{fold}.parquet',f0/f'exclude_fold{fold}/observation_link_{line}.parquet',f0/f'exclude_fold{fold}/peril_cost_shares_{line}.json']
        paths += [ROOT/old['base_model_runs'][mid]/'models'/f'{mid}_{line}_fold{fold}/bundle.joblib' for mid in ['W2-B00','W2-B12','W2-B14']]
plan={'id':'S2-C0-MEZCLA-NEGOCIO2023-v1-20261024','author':'Codex','registered_utc':datetime.now(timezone.utc).isoformat(),
 'authorization_literal':'Dale, revisa la mezcla de C0 por peril y tipo de negocio. Registra la prueba solo en 2023 con modelos estándar, conserva B00, deja las decisiones y resultados en el foro y mantén 2024 cerrado.',
 'hypothesis':'A single line-level peril-cost mixture may differ between newbusiness and renewal. Isolate frequency composition and then severity composition while holding pooled peril count/cost completion curves fixed.',
 'input_run':rel(v6),'base_oof':idx['oof'],'base_model_runs':old['base_model_runs'],'observation_run':rel(f0),'claim_source_2023':rel(claim_source),'code':rel(code),'code_sha256':sha(code),
 'selection_policy':old['selection_policy'],'selection_policy_sha256':old['selection_policy_sha256'],'main_model_index':rel(main),'main_model_index_sha256':sha(main),
 'prior_sensitivity_index':rel(prior),'prior_sensitivity_index_sha256':sha(prior),'counter_index':rel(counters),'counter_before_sha256':sha(counters),'counters_before':co,
 'variants':{'MIXF':'Within own2023 outer-training line/business, Poisson intercept rate lambda_pb=n_pb/sum(exposure*qN_p). Keep pooled-peril positive severity mu_p. Normalize costs lambda_pb*mu_p across perils to weights; q_mix_b=sum(weight_pb*qC_p).',
  'MIXFS':'Same lambda_pb, but weighted Gamma-intercept positive mean mu_pb=sum(truncation_weight_i*T0_i)/sum(truncation_weight_i), using frozen ownfold C0 severity_probability_weight. Normalize lambda_pb*mu_pb. No smoothing, prior, selected blend or new curve.'},
 'zero_rule':'n_pb=0 gives Poisson boundary rate0 and costweight0; positive severity is not estimated (null), never interpreted as no future risk. For n>0, zero/invalid weight mass or nonpositive mean fails closed, no heldout fallback. Each business totalcost must be positive.',
 'curves':'Reuse exact ownfold2023 pooled qN_p and qC_p plus truncation weights, and prove pooled reconstruction matches baseC0. No per-business curve fit. Still conditions on common report/cost timing and a broad at-risk exposure denominator; no individual coverage masks.',
 'models':['W2-B00 line constant','W2-B12 line/business constants','W2-B14 exact sixfeature alpha0Tweedie1.5GLM'],
 'price_objective':'UnchangedT0, responseT0/e_mix, weight sqrt(e_mix), predictione_mix*rate, ownfold2023 only. Mixture uses normalized shares, never the total frequency*severity as an extra pricing multiplier. No feature, capital, climate, credibility or calibration change.',
 'partitions':'2023 only,50094periods,30869components,5persistedfolds, disjoint customers/addresses/components; no reseed.',
 'numerical_link_identity_atol':1e-12,
 'reuse_rule':'When maxabsolute effective-exposure difference across whole2023line/fold <=1e-12, copy baseline native bundle exactly and report numerical link identity; this is computational reuse, not statistical equivalence.',
 'readout':['Peril/business trainingcounts, effective exposure, lambda, severity, weight effective sample size, largest weighted cost share and zeros; do not report5fold repetitions as independent claims',
  'Mixture shares byfold/line/business and difference between groups; e_mix/e_base OOF distribution and base pooled reproduction',
  'Global/line/fold/business D2 and A/E, observed/predicted and nominalconditioned2023 totals; same labels/rows, no2025/test prediction',
  'Publish sparse/extreme and adverse results; earlier tail/reserve/report-stress retained without repeating its fits or bootstrap'],
 'bootstrap':{'replicates':2000,'seed':2026102302,'pairs':'Twelve:3family pairs within eachMIXF/MIXFS (6),3MIXF/ownbase,3MIXFS/MIXF. CommonT0/globalnull and samegroup draws; own31 favorablegroup removal. No old pair distributions repeated.','interval':'Unadjusted exploratory95% percentile, not simultaneous or temporal confirmation.'},
 'technical_acceptance':['2023 source hashes, scope and claimweight reconciliation beforefit; no heldout claims in mixture','Rebuilt pooled lambda*mu shares equal baseC0; new weights nonnegative,sum1 and epositive<=nominal',
  'Independent calculation of count exposure, Poisson/Gamma intercept means, truncationweights and mixture convex sums; explicit zero cells and sparse effective counts',
  'Native replay blockedfit, numeric imputers fit-only, scalarpriceconstant optimum and GLMscore<=1e-4','Twelve new pairedbootstrap and own31 influence reconstructed separately; all50094keys/sharedT0',
  'Main19catalog/B00/allalternatives exact,2024/test closed and ledger absent'],
 'decision_rule':'No adoption of business mixture or model by2023 point, no tuning a smoothing strength after scores, no promotion/retirement/equivalence/final roster. Technical correctness is not ultimate validation.',
 'resources':'Local2threads, max30newpriceGLMfits and90priceconstantvalues, less numericalidentity reuses. Separate150Poisson business/peril frequency constants and up to150weightedpositive severity means, shared between variants;0newreportcurve/credibilityfits. Start ownpricecounters135/195 and add actual only.',
 'limits':['Sparse accepted claims and few dominant groups can destabilize unshrunk business severity/mix; zeros do not prove no risk.',
  'Pooled per-peril report/cost CDFs remain an assumption even after splitting mixture weights; individual coverage/peril exposure masks not introduced.',
  'Severity correction weights come from pooled truncated delay distribution, not proof of business-specific delay/cost independence or missing-tail truth.',
  'Grouped2023 at2024-12-31 is not information at beginning2023; no prospective validation or2025 ultimate labels.',
  'Sensitivity changes observationlink, not a new candidate under frozen commonC0; comparefamilies within samevariant and preserve originalB00. Own technical review, not independent professional validation.'],
 'frozen_sources':[{'path':rel(path),'sha256':sha(path)} for path in dict.fromkeys(paths)],'forum_preregistration':'COD-S2-20261024-027','reference':'W2-B00','confirmation_2024_open':False}
path=REPO/'registro/semana2_c0_mezcla_negocio2023_plan_v1.json';dump(path,plan)
body='''Codex. Continúo 026 por solicitud directa de revisar la mezcla de C0 por peril y negocio. El [plan](../../Repositorio_IAA2026/registro/semana2_c0_mezcla_negocio2023_plan_v1.json) registra dos sensibilidades antes de ajustar o puntuar. Se conservan las pruebas de cola, reservas y coste tardío sin repetirlas.

MIXF estima por ramo y negocio la frecuencia de cada peril: lambda=n/suma(exposición×qN_peril), constante Poisson de ajuste. Mantiene la severidad media y las curvas qN/qC por peril del C0 original. Normaliza lambda×severidad para obtener pesos de mezcla y calcula e_mix=exposición×suma(peso×qC). MIXFS cambia también la severidad media por negocio, con el promedio Gamma de costes positivos ponderado por los pesos de truncamiento del propio fold ya guardados. Ambas reutilizan las mismas constantes de frecuencia; no se ajustan curvas por negocio.

Se conserva el efecto de negocio en precios de B12/B14 y la misma receta estándar. La primera etapa aporta solo pesos normalizados de peril, nunca un multiplicador adicional de frecuencia×severidad. Se comprobará que agrupar de nuevo reproduce el C0 pooled. Los parámetros se estiman exclusivamente en el ajuste2023 de cada fold; el negocio de cada fila es conocido en cotización. No hay calibración OOF o datos del retenido en los pesos.

No se elige una intensidad de contracción o mezcla por score. Una celda con cero siniestros tiene frecuencia estimada cero y peso cero; no se estima su severidad ni se interpreta como ausencia futura de riesgo. Si una celda positiva tiene masa de ponderación nula o inválida, la prueba se detiene sin fallback con validación. Se publicarán conteos, tamaño efectivo y concentración para no esconder la fragilidad de las celdas pequeñas. La curva de reporte/coste sigue siendo compartida por peril, y no se añaden máscaras individuales de cobertura.

Mismos T0, 50.094 periodos de 2023, 30.869 componentes y cinco folds. B00 constante, B12 constante por negocio y B14 GLM pequeño alpha0, seis variables. Respuesta T0/e_mix, peso sqrt(e_mix), observado=e_mix×tasa y nominal condicionado=exposición2023×tasa. No son precios de2025/test o etiquetas últimas. Se reutiliza exactamente el modelo nativo si el enlace completo difiere como máximo1e-12, tolerancia computacional previa, no declaración de equivalencia estadística.

Máximo30GLM/90constantes de precio nuevos; aparte150constantes Poisson de mezcla y hasta150medias de severidad ponderada, sin duplicarlas entre variantes. Cero curvas de reporte o auxiliares de credibilidad nuevos. Contador inicial135ajustes de precio/195constantes; se suma solo lo realizado. Doce contrastes nuevos con2.000sorteos comunes: tres familias dentro de cada variante, MIXF frente a sus tres padres y MIXFS frente a MIXF; mismoT0/nula, influencia propia de31grupos. Sin repetir remuestreos anteriores.

Criterio técnico: fuentes/ámbitos íntegros, reproducción pooled, pesos convexos, exposición positiva, verificador separado de medias/ponderación/días expuestos, replay sin fit, óptimos/gradientes, ámbitos y12remuestreos. Criterio de decisión: publicar resultados adversos y celdas escasas, conservar B00/todas las alternativas, sin adopción, promoción, retiro, equivalencia o lista final por un punto2023. Revisiones propias de Codex, no profesionales independientes; siguen abiertas cola, reservas, dependencia coste/reporte y disponibilidad temporal.

2024 cerrado expresamente: sin precios, predicciones, scores o ledger de ese año o test. Sin remoto, envíos, publicación externa, nuevos chats, delegación o cambios a otras automatizaciones. El catálogo principal de19recetas conserva su corte; estas seis configuraciones van al índice específico de sensibilidad.
'''
with (FOLDER/'mezcla_negocio2023_preinscripcion.md').open('x',encoding='utf-8') as f:f.write(body)
night=REPO/'registro/semana2_continuidad_nocturna.json';before=night.read_bytes()
with (FOLDER/'nocturno_antes_mezcla_negocio2023.json').open('xb') as f:f.write(before)
n=read(night);assert n['current_unit'] is None;n.update(status='sixth_unit_in_progress',updated_utc=plan['registered_utc'],current_unit={'id':plan['id'],'plan':rel(path),'status':'preregistered_do_not_relaunch_without_checking_run','forum_preregistration':plan['forum_preregistration']})
assert night.read_bytes()==before;tmp=night.with_suffix('.mezcla.tmp');tmp.write_text(json.dumps(n,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');os.replace(tmp,night)
print(json.dumps({'plan':rel(path),'sha256':sha(path)}))
