"""Octava unidad: hipótesis de cobertura antes de cruzar siniestros."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()
NOW=datetime.now(timezone.utc).isoformat();OWN=ROOT/'Hackaton/Semana 2/Codex'
night=REPO/'registro/semana2_continuidad_nocturna.json';before=night.read_bytes();n=read(night)
assert n['current_unit'] is None and len(n['completed_units'])==7
mix=ROOT/read(REPO/'registro/semana2_sensibilidad_observacion_actual.json')['run'];mp=read(mix/'plan_snapshot.json')
base=ROOT/mp['input_run'];obs=ROOT/mp['observation_run'];code=REPO/'src/semana2/auditar_coberturas_peril2023.py'
paths=[code,REPO/'registro/semana2_desarrollo2023_actual.json',REPO/'registro/semana2_sensibilidad_observacion_actual.json',REPO/'registro/semana2_contadores_propios_actual.json',
       REPO/'registro/semana2_soporte_calendario2023_actual.json',mix/'inputs_2023/claims_2023.parquet',OWN/'fuentes_variables_ultimo/data_description_response.json']
for line in ['motor','buildings','contents']:
    paths.extend([base/f'inputs_2023/{line}.parquet',base/f'inputs_2023/raw_{line}.parquet'])
    paths.extend(obs/f'exclude_fold{k}/observation_link_{line}.parquet' for k in range(5))
plan={'id':'S2-COBERTURAS-PERIL2023-v1-20261024','author':'Codex','registered_utc':NOW,
 'authorization_literal':'Dale, revisa las coberturas y los denominadores de exposición por peril. Registra cualquier prueba solo en 2023 con modelos estándar, conserva B00, deja las decisiones y resultados en el foro y mantén 2024 cerrado.',
 'hypothesis':'Broad line/business exposure is an approximation for peril denominators. Test plausible coverage masks against observed claims before treating coverage labels as structural zeros or shrinking denominators.',
 'period_input_run':rel(base),'mixture_run':rel(mix),'observation_run':rel(obs),'code':rel(code),'code_sha256':sha(code),'forum_prior':'COD-S2-20261024-032',
 'frozen_sources':[{'path':rel(q),'sha256':sha(q)} for q in sorted(set(paths))],
 'evidence_scope':'Archived official dictionary lists motor cover categories, optional accidental damage and optional bicycle. It gives no complete policy wording or coverage-peril crosswalk. Label interpretations are candidate hypotheses, not authoritative exclusions.',
 'candidate_masks':{'motor':{'own_damage':'comprehensive only, conventional hypothesis','glass_hail':'comprehensive only, composite-peril conventional hypothesis','theft':'comprehensive or third_party_fire_theft, conventional hypothesis','third_party_prop':'all','bodily_injury':'all'},
     'buildings':{'accidental_damage':'accidental_damage_cover=True, plausible optional-cover match','other_perils':'all'},
     'contents':{'accidental_damage':'accidental_damage_cover=True, plausible optional-cover match','other_perils':'all','bicycle':'Category audit only. Never map bicycle_cover to all theft or all accidental_damage.'}},
 'denominators':'For each owntraining fold/line/business/peril, D_all=sum(exposure*qN_peril); D_candidate=sum(mask*exposure*qN_peril). Also nominal and cost-completion exposure partitions. No frequency fitted: D_all/D_candidate is only an exposure ratio, not a new risk rate or price. Use corrected F0 nominalexposure, not raw exposure or count of rows.',
 'numerator':'Keep canonical included2023claims and netcents unchanged. Count inside/outside candidate, positive and zero-cost claims, status/positive-status, grouped denominator categories. Retainedfold claims never enter training views. Full-cohort report descriptive only, not new fit.',
 'criterion':'No candidate adopted in this diagnostic. Any positive netcost outside a mask refutes its compatibility with current target; zero outside-cost is only necessary, not proof of contract or future no risk. Reject denominator-only shrink with unchanged mismatched numerator. Do not drop/relable claims, statuses or covers. Unknown/missing cover fails closed. Preserve all sparse/empty cells and alternatives.',
 'verification':'Separate dictionary-loop and math.fsum implementation of joins, conditional nominal/count/cost sums and claim partitions; fixed curves, year/group scope and source hashes. Real native guard fixtures for year and missing cover. Technical algebra fixtures for all-ones mask, additive partitions, empty masks and no inferred bicycle/theft mapping. No prior suite or bootstrap repetition.',
 'resources':'Local<=45min; zero price/curve/auxiliary fitting, zero scores/bootstrap. Ownpricecounters165/285 unchanged, other stages separate.',
 'limits':['No contract matrix inferred from zero counts or names alone','No row-specific true coverage proof from an exposure ratio','Known truncated claims and data semantics can conflict; report apparent mismatch, not fraud or automatic data deletion','Header exposure to external2024 outcomes already disclosed; no complete blindness claim, no external outcome used'],
 'reference':'W2-B00','confirmation_opened_by_this_task':False,'ledger_read':False,'professional_independent_validation':False}
pp=REPO/'registro/semana2_coberturas_peril2023_plan_v1.json'
with pp.open('x',encoding='utf-8') as f:json.dump(plan,f,ensure_ascii=False,indent=2);f.write('\n')
with (OWN/'nocturno_antes_coberturas_peril2023.json').open('xb') as f:f.write(before)
n.update(status='eighth_unit_coverage_denominator_diagnostic_in_progress',updated_utc=NOW,current_unit={'id':plan['id'],'plan':rel(pp),'status':'preregistered_zero_fits_scores','forum_preregistration':plan['forum_prior']})
tmp=night.with_name(night.name+'.coberturas.tmp')
with tmp.open('x',encoding='utf-8') as f:json.dump(n,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
assert night.read_bytes()==before,'Concurrencia';os.replace(tmp,night)
body='''Por instrucción directa del participante se registra una revisión solo de 2023 de coberturas y denominadores por peril. B00 y todas las alternativas quedan intactos. Hipótesis: la exposición de todo el ramo/negocio puede ser una aproximación demasiado amplia, pero no se restringirá por nombres de coberturas sin cotejar los siniestros y el alcance documental.

El diccionario oficial archivado enumera tres coberturas de autos y coberturas opcionales de daño accidental y bicicleta; no contiene una matriz contractual completa por peril. Como hipótesis, se contrastan daño propio y glass_hail en comprehensive, robo en comprehensive/third_party_fire_theft y daño accidental de hogar con su bandera activa. El resto mantiene toda exposición. Son máscaras candidatas, no exclusiones aprobadas. Bicycle_cover se describe por categorías, sin equipararlo a todo robo o daño accidental.

Para cada ramo/peril/negocio/fold de ajuste, se concilian D_all=Σ exposición×qN y D_candidate=Σ máscara×exposición×qN, además de nominal y coste. D_all/D_candidate es solo una razón de denominadores, no un factor de precio o riesgo estimado. Se usa exposición nominal corregida de F0. Los siniestros canónicos y sus costes netos se conservan: se cuentan dentro y fuera, positivos y de coste cero, con status. El perfil global es descriptivo; el retenido no entra en las vistas de ajuste.

Criterio previo: ningún ajuste, curva, máscara o precio se adopta en esta unidad. Un coste positivo fuera de la máscara impide tratarla como cero estructural compatible con T0; cero costes fuera tampoco demuestra contrato o ausencia futura. No se arregla una incompatibilidad borrando reclamaciones, cambiando status o reduciendo solo el denominador. Faltantes/categorías desconocidas se rechazan, y se conservan celdas vacías y resultados adversos. La comprobación separada usa bucles, fsum, particiones y adversos en el flujo real. Coste previsto cero ajustes, scores o bootstrap; contador propio 165/285 sin cambio.

Plan congelado: `Hackaton/Repositorio_IAA2026/registro/semana2_coberturas_peril2023_plan_v1.json`. Se mantiene el incidente anterior de un título ajeno con métricas de 2024, sin repetirlas ni usarlas; no se afirma ceguera completa. El lector solo muestra autor, ID y UTC. No se abre ledger, acta o predicciones de 2024/test ni otra tanda; sin remoto, envíos o delegación. Revisión técnica propia, no profesional independiente.
'''
with (OWN/'coberturas_peril2023_preinscripcion.md').open('x',encoding='utf-8') as f:f.write(body)
print(json.dumps({'plan':rel(pp),'sha256':sha(pp),'sources':len(paths),'no_new_fits_scores':True}))
