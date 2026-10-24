"""Receta de sensibilidad de C0/reservas registrada antes de ajustar o puntuar."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,os
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
def dump(p,o):
    with p.open('x',encoding='utf-8') as f:json.dump(o,f,ensure_ascii=False,indent=2);f.write('\n')
main=REPO/'registro/semana2_desarrollo2023_actual.json';idx=read(main);assert idx['id']=='S2-DEV2023-v7-20261024'
prior=REPO/'registro/semana2_sensibilidad_observacion_actual.json';counters=REPO/'registro/semana2_contadores_propios_actual.json';nread=read(counters)
assert read(prior)['id']=='S2-COLA2023-v1-20261024' and nread['cumulative_price_base_fits']==100 and nread['cumulative_closed_form_constants']==90
v6=ROOT/read(ROOT/idx['plan'])['parent_run'];v5=ROOT/read(v6/'plan_snapshot.json')['parent_run'];v1=ROOT/idx['history'][0]['run'];f0=ROOT/read(REPO/'registro/semana2_listo_entrenar.json')['run'];base=read(REPO/'registro/semana2_preparacion_actual.json')
code=REPO/'src/semana2/sensibilidad_c0_reservas2023.py';folder=ROOT/'Hackaton/Semana 2/Codex'
for source,name in [(prior,'sensibilidad_antes_c0_reservas2023.json'),(counters,'contadores_antes_c0_reservas2023.json')]:
    with (folder/name).open('xb') as f:f.write(source.read_bytes())
paths=[main,ROOT/idx['oof'],ROOT/base['claim_audit'],ROOT/base['target'],ROOT/base['partitions'],code,REPO/'src/semana2/variables_ultimo.py',REPO/'src/semana2/entrenar_desarrollo2023.py',REPO/'src/semana2/entrenar_desarrollo2023_v5.py',
  v6/'plan_snapshot.json',ROOT/read(v6/'plan_snapshot.json')['selection_policy'],folder/'sensibilidad_antes_c0_reservas2023.json',folder/'contadores_antes_c0_reservas2023.json']
for line in ['motor','buildings','contents']:
    paths += [v6/f'inputs_2023/raw_{line}.parquet',v6/f'inputs_2023/{line}.parquet']
    for fold in range(5):
        paths += [v6/f'variant_inputs/{line}_fold{fold}.parquet',f0/f'exclude_fold{fold}/reporting_models.json',f0/f'exclude_fold{fold}/reporting_fit_claims.parquet',f0/f'exclude_fold{fold}/peril_cost_shares_{line}.json',f0/f'exclude_fold{fold}/observation_link_{line}.parquet']
        paths += [run/'models'/f'{mid}_{line}_fold{fold}/bundle.joblib' for mid,run in [('W2-B00',v1),('W2-B12',v5),('W2-B14',v6)]]
plan={'id':'S2-C0-RESERVAS2023-v1-20261024','author':'Codex','registered_utc':datetime.now(timezone.utc).isoformat(),
 'authorization_literal':'Dale, revisa el nivel agregado, la cola y la sensibilidad de C0 a reportes tardíos y reservas. Registra la prueba solo en 2023 con modelos estándar, conserva B00, deja los resultados en el foro y mantén 2024 cerrado.',
 'hypothesis':'Reserve uncertainty changes both the outcome and cost-mark observation link; late-cost concentration may influence C0 independently of the price fit. Standard constants and alpha0 GLM suffice to isolate those mechanisms.',
 'input_run':rel(v6),'base_oof':idx['oof'],'base_model_runs':{'W2-B00':rel(v1),'W2-B12':rel(v5),'W2-B14':rel(v6)},'observation_run':rel(f0),'claim_audit':base['claim_audit'],
 'code':rel(code),'code_sha256':sha(code),'selection_policy':read(v6/'plan_snapshot.json')['selection_policy'],'selection_policy_sha256':read(v6/'plan_snapshot.json')['selection_policy_sha256'],
 'main_model_index':rel(main),'main_model_index_sha256':sha(main),'prior_sensitivity_index':rel(prior),'prior_sensitivity_index_sha256':sha(prior),
 'counter_index':rel(counters),'counter_before_sha256':sha(counters),'counters_before':nread,
 'scenarios':{'R075':'Target T0−.25*reserve and ownfold saved e_cost_mix_0.75, whose cost-CDF and costshares use the same mark. Refit each standard model.',
   'R125':'Target T0+.25*reserve and ownfold saved e_cost_mix_1.25, same matched mark convention. Refit each standard model.',
   'L1':'Target T0. In each line/fold choose the outer-training graph component with largest sumT0_cents among accepted assigned claims with delay>365days, ties lexicographic group_id. Remove all that component claims AND periods only from C0 reporting/mixture estimation. Refit original reversed-truncation count/cost curve and peril shares from remaining owntraining2023. Price fit retains every original trainingperiod, including removed reportingcomponent. If no latecost component exists, use exactbase link. No fallback from validation or lostperil/min5 failure.'},
 'models':['W2-B00 line constant','W2-B12 line/business constants','W2-B14 original six-feature alpha0Tweedie1.5GLM'],
 'price_objective':'T_s/e_s response, sqrt(e_s) weights, e_s*annual_rate observed prediction. Exact sixfeatures/core/parameters ofB14, no calibration/credibility/climate or capital change. Copies exact if both target and effective exposure unchanged throughout line/fold.',
 'partitions':'2023 only,50094periods,30869components,5savedfolds; customers/addresses/components disjoint. No reseed.',
 'readout':['Pooled D2 under own target, A/E, observed/predicted and conditional nominal2023 totals; line/fold/business/cold segments',
  'Reconcile reserve target difference with accepted canonical reserve cents; identify late-positive counts, latecost share and selected report component',
  'Report C0 costCDF/perilshare/completion changes, and L1 ownbase predicted/nominal rates without excluding priced rows',
  'Prior tail T10F/T10R findings reused by reference, not repeated; nominal2023 is conditional full-observation scale, not2025/test or actual ultimate'],
 'bootstrap':{'replicates':2000,'seed':2026102302,'pairs':'Twelve only:3family contrasts within each ofR075,R125,L1 plus3L1/ownbase. Own target/global null per scenario. No direct reserve-target versusbase superiority contrast, no repeated historic bootstrap.','interval':'Unadjusted exploratory percentile95%, own31 favorablegroup removal. Not temporal confirmation.'},
 'technical_acceptance':['Frozen scope/sources beforefit/score; matched reserve mark/target/link','Late group selection sees only owntraining claims; both exposure and claims removed fromreport fit, none removed fromprice fit',
  'Independent reverse-truncation/perilcost-CDF formula and direct eligible-day completion, no producer import; canonical cents reconcile',
  'Native replay blockedfit, scalar-constant optimum, GLM mean score<=1e-4 and no convergence warning','12new pairedbootstrap reconstructed with multiplicities and scenario-specific null; complete sharedkeys',
  'Current B00/all18alternatives and main catalog exact;2024/test closed and ledger absent'],
 'decision_rule':'No reserve factor, removedgroup policy, reporting curve or candidate adopted from a2023 point. Keep all artifacts and adverse results. No promotion, retirement, equivalence or final roster.',
 'resources':'Local2threads, up to45newGLMfits and135closedformconstantvalues across3scenarios, less exactidentity reuses. New L1 reporting fits recorded separately,0newcredibilityauxfits. Start counters100pricefits/90constants; add actual counts once.',
 'limits':['Reserve marks conditional, not reserve adequacy or ultimate truth. Changing target changes the D2 estimand; cross-target point differences are descriptive only.',
  'L1 is a onecomponent reporting-estimator stress, not full-pipeline deletion/refit or a rule to suppress expensive claims; fixedzero beyond-support tail convention remains.',
  'C0 remains a line-level peril mixture; time/report/cost dependence and missing-tailmass not identified; grouped2023 at2024-12-31 not a backtest at beginning2023.',
  'Own technical review, not independent professional validation. Prior capital/climate/credibility conditions preserved.'],
 'frozen_sources':[{'path':rel(path),'sha256':sha(path)} for path in dict.fromkeys(paths)],'forum_preregistration':'COD-S2-20261024-025','reference':'W2-B00','confirmation_2024_open':False}
path=REPO/'registro/semana2_c0_reservas2023_plan_v1.json';dump(path,plan)
body='''Codex. Continúo024 por solicitud directa de revisar nivel agregado, cola y sensibilidad deC0 a reportes tardíos/reservas. La prueba de cola ya está terminada y conserva su resultado: el mismo score observado admite otra escala nominal condicionada. No se repite. El [plan nuevo](../../Repositorio_IAA2026/registro/semana2_c0_reservas2023_plan_v1.json) fija tres contrastes antes de ajustar o puntuar.

R075/R125 cambian a la vez la respuesta T0+(b−1)reserva y el enlace C0 de marcas de coste/peril correspondiente a b=0,75/1,25, calculado en el ajuste propio. Se reajustan los mismos modelos estándar B00, B12 y B14. Cambiar la respuesta cambia el estimando: no se elegirá b por comparar D² de targets distintos.

L1 mantieneT0 y aísla la primera etapa. Por ramo/fold se escoge solo entre los componentes de ajuste el de mayor coste asignado positivo con demora>365días, con empate porID. Se retiran todas sus reclamaciones y sus exposiciones del ajusteC0; se reestiman las mismas curvas de truncamiento inverso, marcas y pesos por peril con el resto2023. Todos los periodos originales se conservan en el ajuste de precios, incluido ese componente; el retenido no aporta selección o estimación. Si no hay tal componente, el enlace es idéntico. Se detiene ante un peril perdido o menos de cinco observaciones; no hay fallback con validación. Es adverso del estimador de reportes, no una recomendación de excluir costes ni un reajuste integral del pipeline.

Mismos50.094periodos2023,30.869componentes,5folds,T0oT_b según escenario, sqrt(e_s) como peso. B14 conserva las seisvariables y alpha0; no se modifica capital, clima, credibilidad o calibración. Se reutiliza un modelo exacto si tanto respuesta como enlace son idénticos. Máximo45GLM/135constantes nuevos; curvasdereporteL1 por separado, ceroauxiliarescreíbles nuevos. Contador inicial100ajustesprecio/90constantes; se sumará solo lo realizado.

Se publicarán nivel/nominal condicionado de esos mismos periodos2023, A/E/D², ramo/fold/negocio, reserva en centavos y concentración de reporte/coste tardío, cambios de C0 e influencia. Solo12contrastes con2.000sorteos comunes: tresfamilias dentrodecadaescenario yL1frenteasus3padres conT0idéntico. La nula depende del target de cada escenario; no se repetirá el remuestreo anterior. Verificador separado sin productor/fit: fórmula de truncamiento por otro método, completitud por días admisibles, óptimos/gradientes, replay y controles adversos.

Criterio de decisión: conservarB00 y alternativas, publicar pérdidas y condiciones, sin adoptar factor de reservas/grupo excluido/curva por score, sin promoción/retiro/equivalencia o lista final. Nominal2023 es una escala condicionada, no precio2025 o verdadúltima. Las reservas, dependencia coste/reporte, mezcla individual, cola fuera de soporte y disponibilidad temporal siguen condicionadas; revisión propia deCodex, no profesional independiente.

2024 sigue cerrado expresamente, sin entrenamiento deprecio/predicciones/scores deeseaño otest ni ledger. Sin remoto, envíos, publicación externa, nuevoschats o delegación. Se preservan autores y estados de hallazgos ajenos; la programación nocturna existente continúa.
'''
with (folder/'c0_reservas2023_preinscripcion.md').open('x',encoding='utf-8') as f:f.write(body)
night=REPO/'registro/semana2_continuidad_nocturna.json';before=night.read_bytes()
with (folder/'nocturno_antes_c0_reservas2023.json').open('xb') as f:f.write(before)
n=read(night);assert n['current_unit'] is None;n.update(status='fifth_unit_in_progress',updated_utc=plan['registered_utc'],current_unit={'id':plan['id'],'plan':rel(path),'status':'preregistered_do_not_relaunch_without_checking_run','forum_preregistration':plan['forum_preregistration']})
assert night.read_bytes()==before;tmp=night.with_suffix('.c0reservas.tmp');tmp.write_text(json.dumps(n,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');os.replace(tmp,night)
print(json.dumps({'plan':rel(path),'sha256':sha(path)}))
