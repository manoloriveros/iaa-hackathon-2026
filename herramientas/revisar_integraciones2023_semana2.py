"""Diagnóstico de capital, clima y credibilidad; no ajusta ni predice precios."""
from pathlib import Path
from datetime import datetime,timezone,date
import importlib.util,sys,json,uuid,ast,hashlib
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
s=importlib.util.spec_from_file_location('integration_review',REPO/'herramientas/verificar_desarrollo2023_semana2.py')
c=importlib.util.module_from_spec(s);sys.modules[s.name]=c;s.loader.exec_module(c)
pd,pq,np=c.pd,c.pq,c.np
author=ROOT/'Hackaton/Semana 2/Claude/decisiones_20261023';code=author/'aplicar_decisiones.py';tree=ast.parse(code.read_text(encoding='utf-8'))
func={n.name:ast.get_source_segment(code.read_text(encoding='utf-8'),n) for n in tree.body if isinstance(n,ast.FunctionDef)}
active=c.read(REPO/'registro/semana2_desarrollo2023_actual.json');parent=ROOT/active['run'];ev=c.read(author/'evidencia_decisiones.json');raw=ROOT/'Hackaton/Semana 2/Datos/emerging'
out=parent.parent/('revision_integracion_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]);out.mkdir()
checks=[]
def check(n,v):checks.append({'name':n,'pass':bool(v)})
capfile=REPO/'privado/semana2/decisiones_participante_20261023/capital_caps2_01.parquet'
caps=pq.read_table(capfile,filters=[('year','=',2023),('is_test','=',False)]).to_pandas();capital=[]
for line,threshold in [('buildings',5e6),('contents',2e6)]:
 p=pq.read_table(raw/f'policies_{line}.parquet',filters=[('period_start','>=',date(2023,1,1)),('period_start','<',date(2024,1,1))]).to_pandas()
 f=pq.read_table(parent/f'inputs_2023/{line}.parquet').to_pandas();t=caps[caps.line.eq(line)];m=p.merge(t,on=['row_id','policy_id'],suffixes=('','_table'),validate='one_to_one')
 check('Private table arithmetic '+line,np.allclose(m.sum_insured,m.sum_insured_raw) and np.allclose(m.sum_insured_model,m.sum_insured/1000) and m.audit_capital_scale_adjusted.all())
 check('2023 outliers coverage '+line,set(t.row_id)==set(p.loc[p.sum_insured.gt(threshold),'row_id']))
 masked=f[f.row_id.isin(t.row_id)];capital.append({'line':line,'rows_2023':len(t),'masked_in_old_F0':int(masked.x_log_sum_insured.isna().sum()),
  'positive_T0_rows':int(masked.T0.gt(0).sum()),'sum_T0':float(masked.T0.sum()),'source_table_total_rows':pq.ParquetFile(capfile).metadata.num_rows})
 # Only metadata and 2023 rows enter review; no other-year price frame is loaded.
check('Climate future-year selection statically visible','2025' in func['clima'] and 'r2 >= PERSISTENCIA_MIN' in func['clima'])
check('Climate 2023 materialized from 2024','(2023, [2024])' in func['clima'])
auditfile=REPO/'privado/semana2/Validacion_enjambre/runs/20261023T231744Z_datos_ambas_semanas/disponibilidad/clima_adverso_permutacion.json'
check('Received climate adversarial evidence unchanged',c.sha(auditfile)=='1ead4dc466f59ff0f5403322a0570ad718df445820668d5adb2258193a76a97f')
cred=ev['nuevo_negocio'];formula=[]
for fold,record in cred['credibilidad_por_fold'].items():
 for line,r in record['ramos'].items():
  zf=record['tau_f']**2/(record['tau_f']**2+r['se_f_em']**2);zs=record['tau_s']**2/(record['tau_s']**2+r['se_s_em']**2)
  th=zf*r['theta_f_em']+(1-zf)*r['theta_f_dev']+zs*r['theta_s_em']+(1-zs)*r['theta_s_dev']
  check('Received fold credibility algebra '+fold+line,np.allclose([zf,zs,th,np.exp(th-r['theta_em'])],[r['Z_f'],r['Z_s'],r['theta_cred'],r['c']]))
  formula.append({'fold':int(fold),'line':line,'c_received':r['c'],'Z_f':zf,'Z_s':zs})
check('Full factors use all 2023','theta_em' in (author/'factor_nuevo_negocio.py').read_text(encoding='utf-8'))
check('Stored outer factors have excluded fold fitting','pk = prep_e[l][prep_e[l].row_id.map(fold_de) != k]' in func['nb_credibilidad'])
# Dependency proof for calibrating with the other rows of ordinary OOF: their models contain the retained fold.
dependencies=[]
for heldout in range(5):
 for other in range(5):
  if heldout!=other:dependencies.append({'outer_heldout':heldout,'calibration_row_oof_fold':other,'that_model_training_folds':[k for k in range(5) if k!=other],
    'contains_outer_heldout_labels':heldout!=other})
check('Ordinary outer OOF is not nested calibration',len(dependencies)==20 and all(x['outer_heldout'] in x['that_model_training_folds'] for x in dependencies))
result={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'source_run':active['run'],'capital_2023':capital,'received_fold_factors':formula,
 'climate_decision':'Reject CLIMA-S2-01 as prospective 2023 feature: values use2024 and selection uses2025. Keep no-climate reference; do not fit inadmissible price comparator.',
 'credibility_decision':'Recompute emerging coefficients/SE/tau within each outer-training 2023 scope; reuse developed2021-2023 coefficient prior only as frozen received evidence. No whole-2023 c or other-fold OOF balancing; test direct c on unpenalized business main-effect GLM.',
 'capital_decision':'Test divided-capital rule with normal ppm bounds learned only on the relevant outer-training 2023 rows; own record premium only for scale audit, never predictor.',
 'open_limits':['Premium-based scale rule relies on tariff/scale assumption, not independent economic confirmation.','Developed prior raw-data/fit not independently replayed by this trial; its uncertainty and market transfer remain conditions.','Frequency/severity credibility estimates observed positive costs, not proven ultimate or January transferred-business behavior.'],
 'OOF_calibration_dependencies':dependencies,'fit_calls':0,'price_predictions':0,'year':2023,'confirmation_2024_open':False,
 'checks':checks,'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'professional_independent_validation':False,
 'sources':[{'path':p.relative_to(ROOT).as_posix(),'sha256':c.sha(p)} for p in [code,author/'glm_robusto.py',author/'factor_nuevo_negocio.py',author/'evidencia_decisiones.json',author/'tablas/coeficientes_glm_nb.csv',capfile,auditfile,REPO/'registro/decision_semana2_cuatro_20261023.json',Path(__file__)]],
 'current_phase_read':c.read(ROOT/'Preparación/ESTADO_PROYECTO.json')['current_phase']}
(out/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(out/'code_snapshot.py').write_bytes(Path(__file__).read_bytes())
assert result['failed']==0,[x for x in checks if not x['pass']]
print(json.dumps({'review':out.relative_to(ROOT).as_posix(),'capital_2023':capital,'checks':result['passed'],'failed':result['failed'],'fit_calls':0}))
