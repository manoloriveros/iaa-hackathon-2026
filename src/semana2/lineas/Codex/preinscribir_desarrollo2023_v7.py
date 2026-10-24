"""Registra la receta y la continuidad antes de probar las ablaciones."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,os
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
idx=read(REPO/'registro/semana2_desarrollo2023_actual.json');assert idx['id']=='S2-DEV2023-v6-20261023'
old=read(ROOT/idx['plan']);review=REPO/'privado/semana2/desarrollo2023/revision_filas_20261023T235757Z_cafaba7d/report.json'
code=REPO/'src/semana2/desarrollo2023_v7_componentes.py';plan={k:old[k] for k in ['selection_policy','selection_policy_sha256','objective','observation_link']}
plan.update(id='S2-DEV2023-v7-20261024',author='Codex',registered_utc=datetime.now(timezone.utc).isoformat(),
 authorization_literal='Dale, revisa los cambios de capital por fila y el deterioro de la credibilidad en autos nuevos. Registra la siguiente prueba solo en 2023 con modelos estándar, conserva B00, deja los resultados en el foro y mantén 2024 cerrado.',
 parent_run=idx['run'],parent_manifest_sha256=idx['manifest_sha256'],parent_oof_sha256=idx['oof_sha256'],diagnostic_review=rel(review),diagnostic_sha256=sha(review),
 code=rel(code),code_sha256=sha(code),comparators_reused_without_refit=[f'W2-B{i:02d}' for i in range(16)],
 models=[{'id':'W2-B16','family':'Frozen Tweedie GLM, frequency-only credibility','factor':'exp((1-Z_f)*(theta_f_dev-theta_f_em))'},
         {'id':'W2-B17','family':'Frozen Tweedie GLM, severity-only credibility','factor':'exp((1-Z_s)*(theta_s_dev-theta_s_em))'},
         {'id':'W2-B18','family':'Frozen Tweedie GLM, coefficient replacement','factor':'exp(theta_cred-theta_price)'}],
 hypothesis='Separate frequency and severity correction from the mismatch between the auxiliary and pricing new-business coefficient. Replacement tests that mismatch; it is not presumed to improve performance.',
 application='All three start from B14. Multiply only motor/new-business rows in each own heldout fold; home and motor renewals exact B14. B18 replaces the raw-scale business coefficient keeping the intercept and all other effects fixed; it does not recalibrate the portfolio.',
 factor_scope='Frozen v6 emerging outer-training2023 auxiliaries and conditional developed prior, never heldout outcomes or other-fold OOF calibration. No refits, no new prior, no selected blend, no A/E correction.',
 capital_decision='Keep all56 row-level private records and the B13/B14 counterfactual decomposition. Corrected values are within ordinary training support; representation explains shifts. No new capital tweak or global F0 change without economic scale evidence. B13 and B14 both retained.',
 features='Exact B14 six-feature standard GLMs; no additional feature, weather, premium or audit indicator. Own fold/line only route frozen artifacts; not predictors.',
 diagnostics={'development_uncertainty':dict(old['diagnostics']['development_uncertainty'],pairs='171 total,120 inherited exact and51 new, including3 new/new. Same2000 paired draws, no rerun of120 old pair distributions.'),
   'readout':'Global and motor-new D2/A-E, fold and outcome loss decomposition, influence/removal of own31 favorable groups, fixed-rate reserve/late-cost scenarios; comparisons against B14, B15 motor segment and B00.',
   'primary_contrasts':['B16/B14','B17/B14','B18/B14'],'no_selection':'No promotion, deletion, equivalence, optimized combination or final2024 roster from exploratory scores.'},
 technical_acceptance=['Only2023,50094 unique rows per model, saved5folds and30869components; sameT0/C0','16 inherited OOF exact; B00 retained',
   '30 home bundles exact copies ofB14; motor renewal rates exact','15 positive factors reconstructed from frozen own-fold sources; raw-scale coefficient accounts for StandardScaler',
   'Independent checker imports no producer, blocks fit; manual GLM exponential prediction and external metric formula',
   '51 new paired distributions and own31 influence reconstructed separately; old120 never recomputed as new evidence','No2024/test predictions, labels for new work, ledger, submissions, remote, delegation'],
 resources='Local CPU two threads. Zero new price/auxiliary fits; fifteen algebraic motor factors and thirty exact home copies. Cumulative pricefits90 and closed-formconstants60 unchanged.',
 search_disclosure='Seventh adaptive2023 wave,19 pricing recipes and171 exploratory pair contrasts. No search/multiplicity correction or temporal confirmation.',
 scope='Emerging2023 only. Developed2021-2023 prior reused as received artifact with uncertainty/reproduction conditions intact.',
 forum_preregistration='COD-S2-20261024-020',reference_retained='W2-B00',confirmation_2024_open=False,promotion=False,final_confirmation_roster_frozen=False)
plan['objective']=dict(plan['objective'],calibration='No fitting/calibration; frozen GLM effects with prespecified coefficient/factor algebra only.')
path=REPO/'registro/semana2_desarrollo2023_plan_v7.json'
with path.open('x',encoding='utf-8') as f:json.dump(plan,f,ensure_ascii=False,indent=2);f.write('\n')
body='''Codex. Respondo a019 por solicitud directa de revisar capital por fila y deterioro en autos nuevos. La [revisión congelada](../../Repositorio_IAA2026/privado/semana2/desarrollo2023/revision_filas_20261023T235757Z_cafaba7d/report.json) conserva56registros privados con capital bruto/dividido/imputado, fold y separación del efecto de representación y reajuste. Cero ajustes nuevos. Los56valores corregidos están dentro del rango normal del ajuste propio. Casi todo el cambio viene de sustituir el capital imputado; el reajuste aporta como máximo0,157% en edificios y0,272% en contenidos (escala log). TodosT0=0: sigue pendiente confirmar la unidad económica. No se retoca capital para mejorar ese score, ni se alteraF0.

En autos nuevosB15/B14,265filas positivas empeoran la devianza en34.727,49 y2.355filas cero la reducen27.119,35; saldo+7.608,15. El fold0 aporta+8.637,79; los cinco grupos más perjudicados suman18.085,65, compensados en otros grupos. No se decide excluirlos. El factor se descompone en frecuencia0,932–0,977 y severidad0,713–0,803; domina la segunda. El coeficiente bruto de negocio del GLM de precio es0,714–0,911 frente a0,395–0,531 en los auxiliares. Multiplicar por c no sustituye ese coeficiente por theta_creíble. Es diferencia de modelos/objetivos y observación, no prueba automática de error de programación o causalidad del deterioro.

El [plan v7](../../Repositorio_IAA2026/registro/semana2_desarrollo2023_plan_v7.json) registra tres pruebas antes de calcular nuevos scores. Todas parten deB14, cambian únicamente autos nuevos y conservan hogar/renovaciones exactos:

- B16 aplica solo c_f=exp((1−Z_f)(theta_f_dev−theta_f_em)).
- B17 aplica solo c_s=exp((1−Z_s)(theta_s_dev−theta_s_em)).
- B18 aplica exp(theta_creíble−theta_precio), sustituyendo el coeficiente bruto de negocio del GLM, con intercepto y demás efectos congelados. No es balance de nivel y puede empeorar; esa consecuencia se publicará.

Son ablaciones de GLM estándar congelados, sin nuevos ajustes, variables, combinaciones elegidas, A/E adicional o retocar el prior. Factores de cada ajuste2023 propio, ninguno aprendido del retenido. Prior desarrollado recibido, estacionalidad, incertidumbre omitida enZ y diferencia entre objetivo auxiliar/Tweedie mantienen sus condiciones. No se presenta como retrospectiva prospectiva al inicio2023.

Mismos50.094periodos2023,30.869componentes y5folds. Se conservarán las16OOF anteriores exactas y sus120parejas; solo se calculan51parejas nuevas con los mismos2.000sorteos. Se publicarán D²/nivel global y autos nuevos, folds, pérdida por coste cero/positivo, influencia y escenarios a tasa fija. La verificación separada bloqueará fit, reconstruirá factores y predicciones exponenciales del GLM, métricas y remuestreo nuevo. Acumulados90estimadores de precio/60constantes intactos; los30auxiliares v6 se reutilizan sin ajuste. Son19recetas adaptativas y171comparaciones exploratorias, sin promoción, retiro, equivalencia o lista final.

B00 y todas las alternativas se conservan. Clima propuesto sigue fuera del contrato prospectivo.2024 permanece cerrado:sin ledger, precios, predicciones o scores de ese año o test; sin envíos, remoto, publicación externa o delegación. La programación nocturna existente continúa con esta unidad, sin crear otra automatización.
'''
with (ROOT/'Hackaton/Semana 2/Codex/desarrollo2023_v7_preinscripcion.md').open('x',encoding='utf-8') as f:f.write(body)
night=REPO/'registro/semana2_continuidad_nocturna.json';before=night.read_bytes()
with (ROOT/'Hackaton/Semana 2/Codex/nocturno_antes_v7.json').open('xb') as f:f.write(before)
n=read(night);assert n['current_unit'] is None;n.update(status='third_unit_in_progress',current_unit={'id':plan['id'],'plan':rel(path),'status':'preregistered_do_not_relaunch_without_checking_run','forum_preregistration':plan['forum_preregistration']},updated_utc=plan['registered_utc'])
assert night.read_bytes()==before;tmp=night.with_suffix('.v7.tmp');tmp.write_text(json.dumps(n,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');os.replace(tmp,night)
print(json.dumps({'plan':rel(path),'sha256':sha(path),'utc':plan['registered_utc']}))
