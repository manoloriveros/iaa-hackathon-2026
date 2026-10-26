"""Cerrar contrato de llamada y atribución antes del primer ajuste real."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,ast
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';OUT=R/'privado/semana2/robustez2023/comparacion_publica_hogar_20261025_v1';old=R/'herramientas/comparacion_publica_hogar2023.py';s=old.read_text(encoding='utf-8')
a="PLAN=R/'registro/semana2_comparacion_publica_hogar_plan_v1.json'";b="PLAN=R/'registro/semana2_comparacion_publica_hogar_plan_v2.json'";assert s.count(a)==1;s=s.replace(a,b)
a="bundle,receipt=m.fit(f,teachers,None,plan['fit_recipe'])";b="bundle,receipt=m.fit(f,teachers,None,{'id':plan['fit_recipe']['model_id'],'tau':plan['fit_recipe']['tau']})";assert s.count(a)==1;s=s.replace(a,b)
a="current=float(inc.loc[mask,'prediction'].astype(float).sum());levels.append({'model_id':variant['model_id'],'line':line,'total':total,'R36_total':current,'relative_level_change':total/current-1,'change_gt5pct_requires_attribution':abs(total/current-1)>.05})"
b="current=float(inc.loc[mask,'prediction'].astype(float).sum());oldpure=None;component=None\n   if line in m.HOMES:\n    oldroot=2*np.sqrt(inc.loc[mask,'prediction'].astype(float).to_numpy())-np.sqrt(base.loc[mask,'prediction'].astype(float).to_numpy());assert (oldroot>0).all();oldpure=float(np.sum(oldroot**2));component={'old_singleteacher_pure_total_recovered_from_own_known50pool':oldpure,'fixed_weight_change_effect_total':oldpure-current if variant['home_weight']==1 else 0.,'joint_region_update_effect_total':total-oldpure if variant['home_weight']==1 else total-current,'sum_exact':True};assert abs(sum([component['fixed_weight_change_effect_total'],component['joint_region_update_effect_total']])-(total-current))<1e-6\n   levels.append({'model_id':variant['model_id'],'line':line,'total':total,'R36_total':current,'relative_level_change':total/current-1,'change_gt5pct_requires_attribution':abs(total/current-1)>.05,'attribution':component,'not_evidence_clearing_2023_gates':True})"
assert s.count(a)==1;s=s.replace(a,b);new=R/'herramientas/comparacion_publica_hogar2023_v2.py';assert not new.exists();new.write_text(s,encoding='utf-8');ast.parse(s)
def funcs(t):return {x.name:ast.dump(x) for x in ast.parse(t).body if isinstance(x,ast.FunctionDef)}
before=funcs(old.read_text(encoding='utf-8'));after=funcs(s)
for name in ['compose','synthetic','forecast','load_quotes']:assert before[name]==after[name]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();p=R/'registro/semana2_comparacion_publica_hogar_plan_v1.json';plan=json.loads(p.read_text(encoding='utf-8'));plan.update(id='S2-COMPARACION-PUBLICA-HOGAR-v2-20261025',utc=datetime.now(timezone.utc).isoformat(),previous_unfitted_draft={'path':rel(p),'sha256':sha(p)},api_contract_correction='Before any realfit,adapt frozen model_id to unchanged GLM id argument;no priceconfigurationchange.',level_attribution='decompose home total difference into known fixed50pool->natural weight effect and regionaljointupdate using own known component;numeric attribution doesnot resolvefailed2023gates')
for row in plan['sources']:
 if row['path']==rel(old):row.update(path=rel(new),sha256=sha(new))
plan['sources'].append({'path':rel(old),'sha256':sha(old)})
for row in plan['sources']:assert sha(ROOT/row['path'])==row['sha256']
p=R/'registro/semana2_comparacion_publica_hogar_plan_v2.json';assert not p.exists()
with p.open('x',encoding='utf-8') as h:json.dump(plan,h,ensure_ascii=False,indent=2)
with (OUT/'plan_v2.json').open('x',encoding='utf-8') as h:json.dump(plan,h,ensure_ascii=False,indent=2)
with (OUT/'preparation_v2_receipt.json').open('x',encoding='utf-8') as h:json.dump({'utc':plan['utc'],'CSVassembly_and_forecast_AST_unchanged':True,'no_real_fit_yet':True,'old_draft_preserved':True,'actual_plan_sha256':sha(p),'new_fits':0},h,indent=2)
print(json.dumps({'plan':rel(p),'sha256':sha(p),'new_real_fits':0,'forecast_and_CSVassembly_unchanged':True}))
