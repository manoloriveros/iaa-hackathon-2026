"""Prueba controlada de capital y credibilidad; clima se somete a guardas temporales."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,copy
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
idx=read(REPO/'registro/semana2_desarrollo2023_actual.json');old=read(ROOT/idx['plan']);plan=copy.deepcopy(old)
review=REPO/'privado/semana2/desarrollo2023/revision_integracion_20261023T233806Z_0bd51230/report.json';author=ROOT/'Hackaton/Semana 2/Claude/decisiones_20261023'
plan.update(id='S2-DEV2023-v6-20261023',registered_utc=datetime.now(timezone.utc).isoformat(),
 authorization_literal='Dale, revisa capital, clima y credibilidad antes de integrarlos. Prueba los cambios solo en 2023 con modelos estándar, conserva B00, deja las decisiones y resultados en el foro y mantén 2024 cerrado.',
 parent_run=idx['run'],parent_manifest_sha256=idx['manifest_sha256'],parent_oof_sha256=idx['oof_sha256'],
 diagnostic_review=review.relative_to(ROOT).as_posix(),diagnostic_sha256=sha(review),
 comparators_reused_without_refit=[f'W2-B{i:02d}' for i in range(14)],
 models=[{'id':'W2-B14','family':'TweedieRegressor','parent':'W2-B13','change':'Fold-trained capital quality rule only; same six-feature GLM and parameters. Motor exact reuse.'},
         {'id':'W2-B15','family':'CredibilityRate','parent':'W2-B14','change':'Multiply new-business annual rate by c from own outer-training emerging coefficients and frozen developed prior. Renewal unchanged; no extra A/E balancing.'}],
 core_recipe=old['models'][1],code='Hackaton/Repositorio_IAA2026/src/semana2/entrenar_desarrollo2023_v6.py',
 auxiliary_code='Hackaton/Repositorio_IAA2026/src/semana2/credibilidad2023.py',forum_preregistration='COD-S2-20261023-018')
plan['capital_rule']={'thresholds':{'buildings':5000000.,'contents':2000000.},
 'fit_bounds':'For each line/fold, normal rows are outer-training2023 capital>0 and <=threshold; learn minimum/maximum of 1000*written_premium/capital there only.',
 'row_test':'For own suspicious row capital>threshold, divide by1000 iff raw ppm<fit minimum and divided ppm lies within fit min/max. Failure remains NaN. Ordinary rows keep previous F0 value.',
 'information':'Own quoted written premium used solely as a scale audit, never a model predictor; no validation distribution, 2024 or test thresholds. It is a tariff-based scale assumption, not economic confirmation.',
 'scope':'2023 only; private CLA table audited arithmetically, not blindly copied for future rows. No original/global F0 edit.'}
plan['credibility_rule']={'reference':'NB-CRED-01 proposed by Claude, adapted to audited training scope; conditional prototype, not a production decision.',
 'developed_prior':'Frozen beta_dev/se_dev from coeficientes_glm_nb.csv and developed seasonal/reference categories from evidencia_decisiones.json (original developed2021-2023 fits). No developed refit or other-year pricing fit in this trial; prior raw fit not independently reproduced here.',
 'emerging_fit':'Recompute Poisson frequency and Gamma positive severity GLMs for each line/outer fold with canonical2023 assigned claims only and original fixed COVS. Capital from this trial, fit-only logcapital median/center and region reference. Fixed developed seasonality. Cluster SE by saved customer-address component.',
 'tau':'As original rule: max(0,mean((betaE-betaD)^2-SE_E^2-SE_D^2)) across matched non-region categorical coefficients with >=100 positive training claims; computed separately frequency/severity, across three training lines only.',
 'Z':'tau2/(tau2+SE_E_newbusiness^2); theta=zF*thetaEF+(1-zF)*thetaDF+zS*thetaES+(1-zS)*thetaDS; c=exp(theta-thetaEF-thetaES).',
 'price_application':'B15=B14*c for new business, B15=B14 for renewal, each line/fold. No ordinary OOF A/E balancing and no full2023 c. B14 unpenalized GLM already has business main effect; c shifts its training-relative level.',
 'technical':'30 auxiliary fits, numerical ridge1e-8, original IRLS max100/tol1e-10, finite positive mean, converged flag and independent mean score <=1e-4. Store coefficients/SE/training data; no silent clipping in pricing.',
 'limits':['Prior coefficient/seasonality uncertainty conditioned on frozen source; Z does not include estimated-prior uncertainty.','Tau uses correlated coefficients and few positives; no calibrated credibility interval or ultimate truth.','Frequency/severity auxiliary objective and cost-mark reporting differ from final Tweedie price objective; common pricing C0 stays fixed.','Ordinary OOF rows from other folds depend on the retained fold, so they are not nested calibration inputs.']}
plan['climate_rule']={'decision':'No prospective price candidate for CLIMA-S2-01: it uses2024 values for2023 and2025 in variable selection.',
 'tests':'Own temporal-availability guards reject source>=quote year, future-dependent selectors and no-history rows. Verify received adversarial evidence hash; do not repeat its permutation over unchanged source.',
 'no_fake_model':'Keep no-climate B00/B13/B14 as references; no identical missing-weather model or leaked-score comparator.'}
plan['objective']['calibration']='No new calibration beyond B14 standard GLM; B15 conditional fold credibility c only on new business, without A/E correction.'
plan['features']='B14 same exact six-feature core as B13; only x_log_sum_insured quality value changes. B15 no added feature. No climate, premium, raw IDs or audit flags as price predictors.'
plan['diagnostics']['development_uncertainty']['pairs']='All120 pairs of16 recipes, shared2000 exploratory draws; independent numerical replay of29 new pairs only, prior OOF exact.'
plan['readout_before_testing']={'capital':'Compare B14 vsB13 on same target/link/rows; report number of restored cells per fold and effect in changed cells separately from other rows. All56 suspicious2023 rows have T0=0; metric cannot economically confirm their scale.',
 'credibility':'Compare B15 vsB14 and B00, c/Z/tau/fold dispersion and new-business line cells, plus aggregate level and own top31 influence. Never substitute a good A/E for deviance.',
 'climate':'Report rejected variants with reason and next admissible source needed; no score with inadmissible weather.',
 'decision':'Keep B00 and all alternatives regardless of point; no promotion, retirement or final roster.'}
plan['technical_acceptance']=['Only2023 emerging materialized for fit/predict/score; no2024/test prices or ledger','Capital bounds learned in outer training, own-row formula and unchanged non-capital predictors','Exact B13 core/parameters and motor reuse','30 auxiliary training-only GLMs, cluster robust SE and score checks; frozen prior identified separately','No held-out targets in c/tau/calibration and no full2023 c reused','Blocked-fit replay, independent formulas, influence/new-pair bootstrap and temporal guards','All14 previous OOF exact and B00 retained']
plan['resources']='Local CPU two threads; ten price GLM fits plus five exact motor reuses, thirty auxiliary Poisson/Gamma GLMs, fifteen c factors/adapters. No grid, remote or reseed.'
plan['scope']='Only emerging2023 price experiments with frozen developed prior artifact. No newly fitted or scored other year, no global F0 rewrite.'
plan['search_disclosure']='Sixth adaptive2023 trial,16 recipes after this wave. Two changes isolated as B14/B13 capital and B15/B14 credibility. No multiple-tuning or confirmation claim.'
plan['frozen_received_sources']=[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in [author/'aplicar_decisiones.py',author/'glm_robusto.py',author/'evidencia_decisiones.json',author/'tablas/coeficientes_glm_nb.csv',REPO/'registro/decision_semana2_cuatro_20261023.json']]
path=REPO/'registro/semana2_desarrollo2023_plan_v6.json'
with path.open('x',encoding='utf-8') as f:json.dump(plan,f,ensure_ascii=False,indent=2);f.write('\n')
body='''Codex. Continúo COD-S2-20261023-017 por solicitud directa del participante de revisar capital, clima y credibilidad y probar cambios solo en2023 con modelos estándar. La [revisión sin ajuste](../../Repositorio_IAA2026/privado/semana2/desarrollo2023/revision_integracion_20261023T233806Z_0bd51230/report.json) pasó25controles. En2023 hay56capitales sospechosos (26edificios,30contenidos), todos enmascarados en F0 y con T0=0. La tabla CAPS2-01 coincide en IDs/valores y división por1000; no demuestra escala económica por score.

El [plan v6](../../Repositorio_IAA2026/registro/semana2_desarrollo2023_plan_v6.json) fija dos variantes antes de ajustar:

- B14: mismo GLM estándar B13 de seis variables por ramo. Solo cambia logcapital: por ramo/fold los límites de prima por mil se aprenden en las filas normales de ajuste2023; cada fila sospechosa pasa su prueba con esos límites. Si no pasa, sigue desconocida. Prima escrita se usa solo para auditar escala, no como predictor. Diez GLM de hogar; autos B13 se conserva exacto. No se copian límites aprendidos con2024/test ni se cambia el F0 global.
- B15: B14 multiplicado por c solo en nuevo negocio; renovación intacta. Se recalculan dentro de cada ajuste2023 los GLM auxiliares Poisson/Gamma de la regla NB-CRED-01, tau y Z. Se reutiliza como prior condicionado el beta_dev/SE y estacionalidad ya guardados por Claude (desarrollado2021–2023), sin reentrenar o puntuar otros años. Las fuentes quedan congeladas; el ajuste desarrollado no se presenta como reproducido aquí. Treinta auxiliares; SE por componente cliente-dirección, referencias/región/mediana/centrado del ajuste. Sin factor c de todo2023, sin equilibrio A/E adicional. La aplicación directa de c es una variante experimental sobre el GLM con negocio no penalizado, no una adopción final de NB-CRED-01.

La dependencia de calibración se deja explícita: aunque se excluyan filas del foldk al promediar OOF, las predicciones de los otros folds se entrenaron conk. No son predicciones internas anidadas sin información de ese fold. Evitaremos ese camino. El prior, tau con coeficientes correlacionados y pocos siniestros, Z sin incertidumbre del prior, y el salto desde coste observado a último permanecen condiciones abiertas.

Clima no entra: CLIMA-S2-01 usa2024 en filas2023 y selecciona variables con correlación2024/2025. Recibí el adverso nuevo COD-S2-VAL04-20261023-CLIMA-AVISO y cotejé su hash sin repetir la permutación. Se harán guardas negativas propias de disponibilidad temporal; no un comparador de precio con fuga ni un modelo duplicado con clima todo faltante. Haría falta historia anterior a la cotización u otro alcance declarado.

Mismos50.094periodos2023,30.869componentes,cincofolds,T0/C0. Se guardarán120parejas con2.000sorteoscomunes,29nuevas reconstruidas separadamente, influencia propia y nivel/segmentos. Las14recetas anteriores y B00 siguen intactas. No promoción o retiro por estos resultados exploratorios. 2024 permanece cerrado, sin ledger, precios/predicciones/scores de ese año o test; no envíos, remoto, publicación externa o delegación. Cada corrección tendrá registro y evidencia, con autoría de Claude preservada.
'''
with (ROOT/'Hackaton/Semana 2/Codex/desarrollo2023_v6_preinscripcion.md').open('x',encoding='utf-8') as f:f.write(body)
night=REPO/'registro/semana2_continuidad_nocturna.json';before=night.read_bytes();(ROOT/'Hackaton/Semana 2/Codex/nocturno_antes_v6.json').write_bytes(before)
n=read(night);n['status']='second_unit_in_progress';n['current_unit']={'id':plan['id'],'plan':path.relative_to(ROOT).as_posix(),'status':'preregistered_do_not_relaunch_without_checking_run','forum_preregistration':'COD-S2-20261023-018'};n['updated_utc']=plan['registered_utc']
assert night.read_bytes()==before;night.write_text(json.dumps(n,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'plan':path.relative_to(ROOT).as_posix(),'sha256':sha(path),'registered_utc':plan['registered_utc']}))
