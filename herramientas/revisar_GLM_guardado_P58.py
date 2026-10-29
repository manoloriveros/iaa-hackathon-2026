"""Diagnóstico nuevo P57: coeficientes, soporte y brecha; cero ajustes o remuestreo."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import json
import math
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p58_saved_GLM',R/'herramientas/validar_GLM_offset_P57.py')
t=importlib.util.module_from_spec(s);s.loader.exec_module(t)
g=t.g;m=t.m;w=t.w;pd=t.pd;np=t.np;BASE=t.BASE
OUT=BASE/'P58_diagnostico_GLM_20261027';PLAN=R/'registro/semana2_GLM_diagnostico_plan.json';INDEX=R/'registro/semana2_GLM_diagnostico_actual.json'
DOC=R/'docs/archivo/semana2/PRIVADA_P58_ESTABILIDAD_GLM.md'


def utc():return datetime.now(timezone.utc).isoformat()
def dump(p,v):return m.dump(p,v)


def main():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    parent=w.read(t.PLAN);m.check_sources(parent);assert w.read(t.OUT/'completion_receipt.json')['report_sha256']==w.sha(t.OUT/'report.json')
    assert not w.read(t.OUT/'report.json')['all_pooled_gates_pass']
    paths=[Path(__file__),t.PLAN,t.OUT/'report.json',t.OUT/'replay_report.json',t.OUT/'completion_receipt.json',g.v.OUT/'report.json']
    for p in t.OUT.glob('*_*/committed.json'):
        d=w.read(p);assert all(w.sha(ROOT/k)==v for k,v in d['outputs'].items());paths += [p,p.parent/'learning.json',p.parent/'prices.parquet']
    sources=dict(parent['sources']);sources.update({w.rel(p):w.sha(p) for p in paths})
    OUT.mkdir();plan={'author':'Codex','utc':utc(),'scope':'All15NEWP57learners: primary coefficient stability in original numeric units and categorical contrasts, training-vs-held loss against matched P55base, positive GROUPsupport per training category. No coefficient/field removal, alpha choice or new validation claim.',
        'prior_information':'P57held losses/gates and its15risk-elasticity coefficients have already been inspected. This diagnostic is not blind or a new confirmatory test.',
        'question':'Do saved coefficients and group support show instability or in-sample advantage not transferred to held groups? This cannot identify its cause or prove that cross-fitting would help.',
        'budget':{'new_GLM_fits':0,'new_source_fits':0,'new_C0_fits':0,'new_resampling':0,'new_saved_model_training_applications':15,'new2025inference':0,'new_submissions':0},
        'interpretation':'Training sets overlap acrossfolds; do not pool as independent evidence or use a training gain as generalization. All adverse groups/categories retained. No oracle scales or selected prices.',
        'sources':sources,'2024_open':True,'B00_all_alternatives_preserved':True}
    dump(PLAN,plan);body=OUT/'forum_previo.md';body.write_text('Codex. P58registra un diagnóstico del GLM P57recién fallido, cuyos scores y15pendientes ya se miraron. Revisaré TODOSlos15ajustes, coeficientes en unidades originales/contrastes categóricos y soporte por grupos positivos; aplicaré los15modelos guardados solo a sus entrenamientos para medir la brecha frente a su propia baseP55. Los conjuntos se solapan: sin inferencia independiente o causal. Cero ajustes, C0, bootstrap,2025o envíos; sin elegir campos/alpha/coeficientes por resultados. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    registration=m.q.post(body,'COD-S2-20261027-PRIVADA-P58-GLM-PREVIO','P58: estabilidad y brecha del GLM guardado, sin reentrenar')
    def reject(*a,**kw):raise AssertionError('P58cannot fit')
    g.fit=reject;g.TweedieRegressor.fit=reject;m.q.cost_curves=reject
    models={line:[w.read(t.OUT/f'{line}_{o}/learning.json') for o in range(5)] for line in m.q.LINES}
    common={line:{name:sorted(set.intersection(*(set(a['preprocess']['levels'][name]) for a in models[line])))[0] for name in g.CAT[line]} for line in m.q.LINES}
    rows=[];coefs=[];support=[];held_gain_total=0.
    for line in m.q.LINES:
        for outer in range(5):
            a=models[line][outer];f=t.frame_for(line,outer);train=f.loc[~f.is_held];held=f.loc[f.is_held]
            u,_=g.forward(train,a);mu=u*train.q_paired.to_numpy();y=train.T0.to_numpy(float);base=train.baseline_observed.to_numpy(float)
            gain=m.e.unit(y,base)-m.e.unit(y,mu);den=m.e.unit(y,np.full(len(y),y.mean())).sum()
            hp=pd.read_parquet(t.OUT/f'{line}_{outer}/prices.parquet').set_index('row_id').loc[held.row_id]
            hy=held.T0.to_numpy(float);hgain=m.e.unit(hy,held.baseline_observed.to_numpy(float))-m.e.unit(hy,hp.new_nominal.to_numpy())
            hden=m.e.unit(hy,np.full(len(hy),hy.mean())).sum();held_gain_total += float(hgain.sum())
            rows.append({'line':line,'outer':outer,'train_rows':len(train),'held_rows':len(held),'train_delta_vs_P55':float(gain.sum()/den),'held_delta_vs_P55':float(hgain.sum()/hden)})
            columns=a['preprocess']['columns'];lookup=dict(zip(columns,a['coef']));d=len(a['preprocess']['numeric'])
            for j,name in enumerate(a['preprocess']['numeric']):coefs.append({'line':line,'outer':outer,'parameter':name,'value':a['coef'][j]/a['preprocess']['scale'][j]})
            for j,name in enumerate(a['preprocess']['numeric']):coefs.append({'line':line,'outer':outer,'parameter':name+'__missing','value':a['coef'][d+j]})
            for name,levels in a['preprocess']['levels'].items():
                reference=common[line][name];values=train[name].astype('string').fillna('__MISSING__')
                for level in levels:
                    coefs.append({'line':line,'outer':outer,'parameter':name+'='+level+' relative '+reference,'value':lookup[name+'='+level]-lookup[name+'='+reference]})
                    z=train.loc[values.eq(level)];tot=z.T0.sum();by=z.groupby('group_id').T0.sum()
                    support.append({'line':line,'outer':outer,'field':name,'level':level,'groups':int(z.group_id.nunique()),
                        'positive_groups':int(z.loc[z.T0.gt(0),'group_id'].nunique()),'largest_group_cost_share':float(by.max()/tot) if tot>0 else None})
    coef=pd.DataFrame(coefs);stability=[]
    for (line,name),z in coef.groupby(['line','parameter'],sort=True):stability.append({'line':line,'parameter':name,'folds_present':len(z),'min':float(z.value.min()),'max':float(z.value.max()),'sd':float(z.value.std(ddof=0))})
    ref=pd.read_parquet(m.REF,columns=['T0']);yy=ref.T0.to_numpy(float);null=m.e.unit(yy,np.full(len(yy),yy.mean())).sum()
    p57=w.read(t.OUT/'report.json')['results']['POOLED']['NOMINAL']['delta'];p55=w.read(g.v.OUT/'report.json')['results']['POOLED']['NOMINAL']['delta']
    assert math.isclose(held_gain_total/null,p57-p55,abs_tol=1e-12)
    m.check_sources(plan);report={'author':'Codex','utc':utc(),'status':'P58new_saved_GLM_diagnostic_complete','scopes':rows,'coefficient_stability':stability,'training_category_group_support':support,
        'training_positive_scopes':sum(z['train_delta_vs_P55']>0 for z in rows),'held_positive_scopes':sum(z['held_delta_vs_P55']>0 for z in rows),
        'global_incremental_GLM_delta_vs_P55':held_gain_total/null,'new_fits':0,'new_resampling':0,'new_training_model_applications':15,'new2025inference':0,'new_submissions':0}
    dump(OUT/'report.json',report)
    next_unit='Before more fields/capacity or alpha changes, preflight a standard TRAIN-ONLYinner evaluation/cross-fitted calibration design, including OWNinner C0and P54base. Never reuse P55pooled base/C0as independent inner learning. Freeze exact cost/criterion and whole outer-validation algorithm before actual learning. The new gap/stability diagnose uncertainty, not a proved cross-fitting benefit or admission.'
    text='# P58: estabilidad y brecha del GLM guardado\n\nCodex, '+utc()+f". El GLMmejora su propio entrenamiento en{report['training_positive_scopes']}de15ámbitos y mejora a su base P55en{report['held_positive_scopes']}de15retenidos. El incremento global frente a esa base es{report['global_incremental_GLM_delta_vs_P55']:+.7f}D². Los entrenamientos se solapan, sin incertidumbre independiente atribuida.\n\n"
    text+='Se guardan todos los coeficientes en unidades originales/contrastes, soporte por grupos positivos y concentración por categoría; no se eliminan o eligen campos. Las15pendientes ya se habían mirado y se declara en el plan. El resultado no identifica causalmente el fallo ni prueba que cross-fitting lo resuelva. Cero ajustes, curvas o remuestreo;15aplicaciones nuevas de modelos guardados al entrenamiento, ninguna2025o envío. B00/F3c/adversos conservados,2024abierto adaptativo.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'.\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':report['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),
        'training_positive_scopes':report['training_positive_scopes'],'held_positive_scopes':report['held_positive_scopes'],'global_incremental_GLM_delta_vs_P55':report['global_incremental_GLM_delta_vs_P55'],
        'new_fits':0,'new_resampling':0,'new_submissions':0,'next_unit':next_unit,'registration':registration,
        'forum':m.q.post(body,'COD-S2-20261027-PRIVADA-P58-GLM-RESULTADO','P58: brecha y coeficientes guardados, sin escoger otro modelo')}
    dump(INDEX,receipt);dump(OUT/'completion_receipt.json',receipt);archive=R/'privado'/('corte_P58_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir()
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P58'),(R/'registro/semana2_mision_privada_actual.json','P58')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P58=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    note='\n\n## Privada P58: diagnóstico del GLM guardado\n\nCodex, '+receipt['utc']+'.Brecha/coeficientes/soporte de15ajustes nuevos; cero entrenamiento/C0/bootstrap/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_GLM_diagnostic_index':w.rel(INDEX),'week_2_private_GLM_diagnostic_report':w.rel(DOC)},archive)
    print(json.dumps({'complete':True,'training_positive_scopes':report['training_positive_scopes'],'held_positive_scopes':report['held_positive_scopes'],'incremental_delta_vs_P55':report['global_incremental_GLM_delta_vs_P55'],'new_fits':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8')
    with m.e.threadpool_limits(limits=2):main()
