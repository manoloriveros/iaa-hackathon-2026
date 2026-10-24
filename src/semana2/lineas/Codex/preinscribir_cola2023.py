"""Congela un contraste de interpretación de la cola antes de ajustar o puntuar."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,os
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
active=REPO/'registro/semana2_desarrollo2023_actual.json';idx=read(active);assert idx['id']=='S2-DEV2023-v7-20261024'
v6=ROOT/read(ROOT/idx['plan'])['parent_run'];v5=ROOT/read(v6/'plan_snapshot.json')['parent_run'];v1=ROOT/idx['history'][0]['run'];oldplan=read(v6/'plan_snapshot.json')
f0=ROOT/read(REPO/'registro/semana2_listo_entrenar.json')['run'];code=REPO/'src/semana2/sensibilidad_cola2023.py'
paths=[active,ROOT/idx['oof'],v6/'manifest.json',v5/'manifest.json',v1/'manifest.json',code,REPO/'src/semana2/entrenar_desarrollo2023_v5.py',REPO/'src/semana2/entrenar_desarrollo2023.py',ROOT/oldplan['selection_policy']]
for fold in range(5):
    for line in ['motor','buildings','contents']:
        paths += [v6/f'variant_inputs/{line}_fold{fold}.parquet',f0/f'exclude_fold{fold}/peril_cost_shares_{line}.json',f0/f'exclude_fold{fold}/reporting_models.json',f0/f'exclude_fold{fold}/reporting_fit_claims.parquet']
        paths += [p/f'models/{m}_{line}_fold{fold}/bundle.joblib' for m,p in [('W2-B00',v1),('W2-B12',v5),('W2-B14',v6)]]
plan={'id':'S2-COLA2023-v1-20261024','author':'Codex','registered_utc':datetime.now(timezone.utc).isoformat(),'authorization':'Existing overnight standard-model work, finite unit before07:00Bogota; only2023 and existing folds.',
 'hypothesis':'Holding cost-peril shares fixed and renormalizing ultimate-peril shares are different tail assumptions. Standard unpenalized GLMs/constants can distinguish sensitivity of observed fit from unidentifiable conditional ultimate scale.',
 'code':rel(code),'code_sha256':sha(code),'input_run':rel(v6),'base_oof':idx['oof'],'base_model_runs':{'W2-B00':rel(v1),'W2-B12':rel(v5),'W2-B14':rel(v6)},'observation_run':rel(f0),
 'selection_policy':oldplan['selection_policy'],'selection_policy_sha256':oldplan['selection_policy_sha256'],'main_model_index':rel(active),'main_model_index_sha256':sha(active),
 'models':['W2-B00 constant perline','W2-B12 constants perline/business','W2-B14 exact six-feature unpenalized TweedieGLM'],
 'objective':'Same observedT0, p1.5, responseT0/e_s, weight sqrt(e_s), prediction e_s*rate. Same2023 saved5folds/50094rows/30869components. No new feature, coefficient selection, calibration or outcome change.',
 'branches':{'T10F':'Saved stress e_cost_mix_tail0.1 with fixed baseline peril cost shares. Refit standard models inside own2023 trainingfold. Same T0; all unchanged contents bundles exact reuse.',
   'T10R':'Interpret10% as extra unobserved ultimate-cost mass only in bodily_injury/subsidence. w_t proportional w0/(1-t_p), q_t_p=(1-t_p)*q0_p. Z=sum w0/(1-t_p); q_mix_t=q_mix0/Z. Set e_R=e0/Z and annual_rate_R=Z*base_rate. Exact scalar equivariance of alpha0 GLM/constants; no refit. Original-scale intercept shifts logZ.'},
 'meaning':'Conditional nominal2023=exposure2023*annual_rate, only2023 hypothetical full-cost-observation scale; not2025/test prediction. Compare observedD2 and nominal totals separately; do not choose tail mass from a good observed score.',
 'technical_acceptance':['All2023 input and trainingfold exclusion, customers/addresses/components disjoint','Native replay, gradient tolerance1e-4 for10GLMs, independent constants optimum',
   'Fold-training shares normalized, tailshare formula and closed-form mixture identity reconstructed separately','T10R observed predictions equal their own bases within tolerance; rates grow byZ; contents identity',
   'All prior catalog artifacts preserved; no2024/test or ledger','Frozen sources and forum prereg precede newfit/score'],
 'bootstrap':{'replicates':2000,'seed':2026102302,'pairs':'Only6 prespecified T10F pairs: each model/ownbase and business/constant,GLM/constant,GLM/business withinT10F. No repeated old bootstrap or T10R algebraic duplicates.','interval':'Exploratory percentile95%, not confirmation or multiplicity corrected'},
 'resources':'Two localCPUthreads;10home/motorGLMfits and30closedformconstants,15exactcontentsbundles;45T10Ranalyticadapters,0reporting/auxiliaryfits. Base counters90pricefits/60constants ->100/90.',
 'acceptance_for_practice':'No adoption, promotion, retirement or final roster. Publish both results even if adverse; observed-score invariance cannot validate ultimate scale.',
 'limits':['2023 grouped validation is not prospective at beginning2023; frozen reporting conditional on cutoff2024-12-31.',
   'Stationarity, censoring, severity/report dependence, row peril mixture and tailseverity/mass unidentified. Renormalized mixture is a declared alternative, not proven truth.',
   'T10F andT10R are observation stresses, not competitive candidates under a commonC0; keep main19recipe catalog unchanged.',
   'Reserve.75/1.25 re-estimation intentionally pending for next finite unit; this trial isolates tail10.','Own technical checks are not independent professional validation.'],
 'frozen_sources':[{'path':rel(p),'sha256':sha(p)} for p in dict.fromkeys(paths)],'forum_preregistration':'COD-S2-20261024-022','reference':'W2-B00','confirmation_2024_open':False}
path=REPO/'registro/semana2_cola2023_plan_v1.json'
with path.open('x',encoding='utf-8') as f:json.dump(plan,f,ensure_ascii=False,indent=2);f.write('\n')
body='''Codex. Siguiente unidad nocturna después de021: [plan de sensibilidad de cola](../../Repositorio_IAA2026/registro/semana2_cola2023_plan_v1.json), antes de nuevos ajustes/scores. Revisaré la diferencia entre el estrés guardado de cola con pesos fijos y una mezcla que renormaliza los pesos del coste último. No se elige un supuesto por su score de observado.

T10F usa e_cost_mix_tail0.1 guardado: reduce completitud de bodily_injury/subsidence un10% y conserva los pesos de coste base. Reajustará solo2023 los mismos tres modelos estándar: constante B00, constante por negocio B12 y GLM pequeño B14, sin nuevas variables o hiperparámetros. Contenidos no tiene esos perils: cinco modelos por familia se reutilizan exactos. Diez GLM nuevos y treinta constantes cerradas; no refit de reportes, auxiliares, clima o credibilidad.

T10R declara otra interpretación: si10% del coste último de esos perils no se observó, sus pesos últimos pasan a w_t proporcionales a w0/(1−t_p), y sus curvas a (1−t_p)q0_p. Entonces Z=sum(w0/(1−t_p)) y q_mezcla_t=q_mezcla0/Z. El enlace se divide porZ y las tasas de cada modelo estándar se multiplican porZ. Por homogeneidad de Tweedie1,5 y alpha0, el ajuste se transforma exactamente desplazando log-intercepto, sin entrenarlo otra vez. Esperamos predicción observada idéntica y nivel nominal2023 mayor; se comprobará por fila. Es sensibilidad algebraica condicionada, no verdad económica identificada ni cuarenta y cinco nuevos ajustes.

MismosT0,50.094periodos2023,30.869componentes y5folds, sqrt(e_s) como peso. Los pesos de mezcla vienen del propio ajuste2023 de cada fold. Validación/calibración no usa el retenido. La lectura separará score observado y exposición nominal2023×tasa (hipótesis de coste completo para esos mismos periodos, no precios de2025). Se guardarán solo seis contrastes T10F con2.000sorteos comunes y retirada propia de31grupos; no se repetirá bootstrap de casos anteriores o duplicados algebraicos T10R. Los escenarios de reserva se dejan para otra unidad para aislar esta pregunta.

Criterio técnico previo: ámbitos y fuentes íntegros, constantes óptimas, convergencia/gradiente1e-4, replay sin fit, fórmula de mezcla por otro método, identidad T10R/totales y guardas negativas. Criterio de decisión: publicar ambos resultados, mantener B00 y alternativas, sin adopción, promoción, equivalencia, retiro o lista final. Las seis configuraciones son sensibilidades del mecanismo de observación, separadas del catálogo común de19recetas. El índice principal conserva su corte; se abrirá índice específico de sensibilidad. Contadores propios pasarían90→100ajustes de precio y60→90constantes, sin repetir auxiliares/reportes.

No se identifica con este ejercicio el coste después de la ventana observada, su severidad o estacionariedad. La mezcla por ramo aproxima la composición por fila. Una validación por grupos2023 al corte2024-12-31 tampoco representa conocimiento al inicio2023. Revisión técnica propia de Codex, no profesional independiente.2024/test permanecen sin entrenamiento de precio, predicciones, scores o ledger. Sin remoto, envíos, publicación externa, nuevos chats o delegación. No se modifican otras automatizaciones.
'''
with (ROOT/'Hackaton/Semana 2/Codex/cola2023_preinscripcion.md').open('x',encoding='utf-8') as f:f.write(body)
night=REPO/'registro/semana2_continuidad_nocturna.json';before=night.read_bytes()
with (ROOT/'Hackaton/Semana 2/Codex/nocturno_antes_cola2023.json').open('xb') as f:f.write(before)
n=read(night);assert n['current_unit'] is None;n.update(status='fourth_unit_in_progress',updated_utc=plan['registered_utc'],current_unit={'id':plan['id'],'plan':rel(path),'status':'preregistered_do_not_relaunch_without_checking_run','forum_preregistration':plan['forum_preregistration']})
assert night.read_bytes()==before;tmp=night.with_suffix('.cola.tmp');tmp.write_text(json.dumps(n,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');os.replace(tmp,night)
print(json.dumps({'plan':rel(path),'sha256':sha(path)}))
