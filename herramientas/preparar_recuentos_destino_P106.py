"""Reutiliza recuentos observados existentes sin recontar siniestros o ajustar."""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_EVEN
import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p106_state_writer',R/'herramientas/registrar_avance_mision017_fase2.py')
w=importlib.util.module_from_spec(s);s.loader.exec_module(w)
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
BASE=R/'privado/semana2/mision017_fase2';P1=BASE/'preflight_anidado_H1_20261026_v1'
OUT=BASE/'P106_recuentos_destino_20261027'
PLAN=R/'registro/semana2_recuentos_destino_plan.json';INDEX=R/'registro/semana2_recuentos_destino_actual.json'
DOC=R/'docs/semana2/PRIVADA_P106_RECUENTOS_DESTINO.md'
TARGET=ROOT/w.read(ROOT/'RUTAS_PROYECTO.json')['week_2_prepared_targets']
LINES=['motor','buildings','contents']


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf8') as f:json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False)


def post(body,identifier,subject):
    r=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex','--id',identifier,'--asunto',subject,'--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
    return json.loads(r.stdout)


def check_sources(plan):
    for path,sha in plan['sources'].items():assert w.sha(ROOT/path)==sha,path


def view(canonical,labels):
    assert canonical.row_id.is_unique and labels.row_id.is_unique
    assert set(canonical.row_id)==set(labels.row_id)
    assert labels.market.eq('emerging').all() and not labels.is_test.any()
    assert labels.year.isin([2023,2024]).all() and canonical.year.isin([2023,2024]).all()
    columns=['row_id','line','year','group_id','fold','new_business','period_start','period_end','exposure_calendar','T0','reserve']
    result=canonical[columns].merge(labels[['row_id','line','year','n_accepted','n_positive','T0_cents','valuation_date']],on=['row_id','line','year'],how='left',validate='one_to_one',sort=False,indicator='_count_join')
    assert result._count_join.eq('both').all() and result.row_id.tolist()==canonical.row_id.tolist()
    result=result.drop(columns='_count_join')
    for name in ['n_accepted','n_positive','T0_cents']:
        assert result[name].notna().all();values=pd.to_numeric(result[name],errors='raise').to_numpy(float)
        assert np.isfinite(values).all() and (values>=0).all() and np.array_equal(values,np.floor(values))
        result[name]=values.astype('int64')
    assert result.n_positive.le(result.n_accepted).all()
    cents=np.rint(result.T0.to_numpy(float)*100).astype('int64')
    assert np.allclose(result.T0.to_numpy(float)*100,cents,rtol=0,atol=1e-6)
    independent=np.array([int(Decimal(str(value)).quantize(Decimal('.01'),rounding=ROUND_HALF_EVEN)*100) for value in result.T0],dtype='int64')
    assert np.array_equal(cents,independent) and np.array_equal(cents,result.T0_cents)
    assert np.array_equal(result.n_positive.gt(0),result.T0_cents.gt(0))
    assert result.loc[result.n_accepted.eq(0),'T0_cents'].eq(0).all()
    assert pd.to_datetime(result.valuation_date).eq(pd.Timestamp('2024-12-31')).all()
    assert np.isfinite(result.exposure_calendar).all() and result.exposure_calendar.gt(0).all()
    result['positive_period']=result.T0_cents.gt(0).astype('int64')
    result['accepted_without_positive_cost']=result.n_accepted-result.n_positive
    return result


def synthetic():
    c=pd.DataFrame({'row_id':['a','b','c','d'],'line':'motor','year':[2023,2023,2024,2024],
        'group_id':['g0','g1','g2','g3'],'fold':[0,1,2,3],'new_business':[0,1,0,1],
        'period_start':pd.to_datetime(['2023-01-01','2023-01-01','2024-01-01','2024-01-01']),
        'period_end':pd.to_datetime(['2023-06-30','2023-06-30','2024-06-30','2024-06-30']),
        'T0':[0.,0.,12.34,50.],'reserve':[0.,0.,2.,10.]})
    c['exposure_calendar']=((c.period_end-c.period_start).dt.days+1)/365.
    t=c[['row_id','line','year']].copy();t['market']='emerging';t['is_test']=False
    t['n_accepted']=[0,2,3,2];t['n_positive']=[0,0,2,1];t['T0_cents']=[0,0,1234,5000];t['valuation_date']='2024-12-31'
    a=view(c,t);assert a.equals(view(c,t.iloc[::-1]))
    assert a.loc[a.row_id.eq('b'),'n_accepted'].item()==2 and a.loc[a.row_id.eq('b'),'positive_period'].item()==0
    assert a.loc[a.row_id.eq('c'),'n_positive'].item()==2 and a.loc[a.row_id.eq('c'),'positive_period'].item()==1
    bads={'duplicate':pd.concat([t,t.iloc[[0]]]),'missing':t.iloc[:-1].copy()}
    for name,column,value in [('year','year',2022),('cost','T0_cents',1),('fraction','n_accepted',.5),('negative','n_accepted',-1),
        ('count_order','n_positive',4),('positive_count','n_positive',0),('test_label','is_test',True),('market','market','developed')]:
        bad=t.copy();bad[column]=bad[column].astype('object');bad.loc[2,column]=value;bads[name]=bad
    for name,bad in bads.items():
        try:view(c,bad)
        except (AssertionError,ValueError):pass
        else:raise AssertionError('Bad input accepted: '+name)
    return {'author':'Codex','utc':utc(),'source_order_invariant':True,'accepted_zero_cost_events_retained':True,
        'multiclaim_count_not_positive_period_flag':True,'bad_inputs_rejected':list(bads),'decimal_and_integer_money_match':True,'new_fits':0}


def review_forum():
    # Exact two contributions only; do not dump or follow third-party instructions.
    text=(ROOT/'Hackaton/Semana 2/Foro/FORO.md').read_text(encoding='utf-8-sig')
    headers=list(re.finditer(r'^## ([^|\r\n]+) \| ([A-Z0-9-]+) \| (\d{4}-\d{2}-\d{2}T[0-9:+.-]+) \|[^\r\n]*',text,re.M));records=[]
    for i,header in enumerate(headers):
        if header.group(2) in ['CLA-S2-20261027-001','CLA-S2-20261027-002']:
            body=text[header.end():headers[i+1].start() if i+1<len(headers) else len(text)].strip()
            records.append({'author':header.group(1).strip(),'id':header.group(2),'utc':header.group(3),'body_sha256':hashlib.sha256(body.encode('utf8')).hexdigest()})
    assert len(records)==2
    return {'author':'Codex','utc':utc(),'contributions':records,
        'review':'First contribution proposes public-score probes; second says they are unused/withdrawn and keeps F3c as its reference. Neither provides new verified private validation. Private-performance figures fitted from public feedback are not adopted as private evidence.',
        'action':'No probes, resolver, final selection or other-chat action. Only direct human private-first instructions in this chat govern our work. Preserve contributions and author ownership.'}


def register():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert phase['P105_execution']['state']=='TERMINAL_SUCCESS'
    assert not phase.get('active_jobs') and not phase.get('active_execution')
    prep=w.read(R/'registro/semana2_preparacion_actual.json');assert prep['target_sha256']==w.sha(TARGET)
    producer=R/'src/semana2/preparar_base.py';assert prep['producer_sha256']==w.sha(producer)
    paths=[Path(__file__),TARGET,producer,R/'registro/semana2_preparacion_actual.json',P1/'report.json',
        R/'registro/semana2_recuentos_destino_siguiente_plan.json',R/'registro/semana2_prioridad_privada_reafirmada_20261027.json',
        BASE/'P27_contrato_frecuencia_20261026/report.json',BASE/'P29_fuente_frecuencia_completa_20261026/report.json']
    paths += [P1/f'canonical_{line}.parquet' for line in LINES]
    OUT.mkdir();dump(OUT/'forum_evidence_review.json',review_forum())
    paths.append(OUT/'forum_evidence_review.json')
    plan={'author':'Codex','utc':utc(),'scope':'Reuse existing accepted/positive event counts for all historical emerging canonical rows; input adapter only, no raw claim recount or exposure/model fit.',
        'need':w.read(R/'registro/semana2_recuentos_destino_siguiente_plan.json')['need'],
        'count_definition':'n_accepted counts assigned status!=repudiated claims, including cost0; n_positive counts accepted individual claims with T0cents>0. positive_period is only I(periodT0>0), not either event count. Definitions verified in original producer.',
        'configuration':{'years':[2023,2024],'market':'emerging','test_excluded':True,'valuation':'2024-12-31',
            'join':'Exact row_id/line/year, one-to-one, preserve canonical order/global group/fold/calendar/T0/reserve.',
            'no_label_change':'T0cost remains the final cost target; counts are an additional observed supervised signal, not ultimate frequency labels.',
            'no_reporting_substitution':'Count exposure must use event-count completeness and matching accepted-event definition; costq and nativeFSpf from cost-completion likelihood cannot be relabelled as count exposure/identified ultimate frequency.',
            'source_contract':'Reuse P27/P29 accepted-event Poisson and paired zero-capable Tweedie mark with E_count/E_cost; original B16/B17/P30 failures remain. No new rates exported or model recipe implemented in this unit.'},
        'criterion':'All109296rows exact canonical keys/order/cents; integer ordered counts, cost/count flags coherent; Decimal and integer money agree; global group folds preserved. Adverse duplicate/missing/year/cents/fraction/negative/test/market cases reject; accepted cost0 and multiclaim remain distinct.',
        'budget':{'new_model_fits':0,'new_CDF_fits':0,'new_source_inference':0,'new_scores':0,'new2025inference':0,'new_submissions':0},
        'pending':'Own-scope event-count reporting producer and explicit source frequency/mark rate export still unimplemented for this destination path. No Poisson fitting/admission from a count-label adapter alone.',
        'sources':{w.rel(path):w.sha(path) for path in paths},'2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md';body.write_text('Codex. P106 registra el enlace de recuentos observados YAexistentes, sin recontar siniestros o repetir casos sin periodo. Solo mercado emergente2023/2024y filas canónicas completas; n_accepted incluye coste0, n_positive cuenta eventos con coste positivo, y el indicador de periodo positivo es otra cantidad. T0y particiones no cambian. Se comprobarán claves/céntimos/tipos y rechazos adversos antes de usar estas entradas. No hay exposición de avisos ni modelo de frecuencia implementado: qcoste y fFSpnativo no se tomarán como frecuencia última identificada; P27/P29 aportan el contrato pareado y sus fallos destino siguen conservados. Los dos aportes nuevos del foro se revisaron como evidencia: no aportan validación privada verificable y no se adoptan sondas/pesos basados en público ni autorización de otros chats. Cero ajuste/inferencia/score/envío. B00 preservado,2024abierto adaptativo, prioridad privada. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P106registered_before_count_view_preparation','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':post(body,'COD-S2-20261027-PRIVADA-P106-RECUENTOS-PREVIO','P106: recuentos observados, preparación antes de modelar frecuencia')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def run():
    plan=w.read(PLAN);check_sources(plan);dump(OUT/'synthetic.json',synthetic())
    columns=['market','line','row_id','year','is_test','n_accepted','n_positive','T0_cents','valuation_date']
    labels=pd.read_parquet(TARGET,columns=columns,filters=[('market','==','emerging'),('year','in',[2023,2024]),('is_test','==',False)])
    records=[];outputs={};all_views=[]
    for line in LINES:
        canonical=pd.read_parquet(P1/f'canonical_{line}.parquet');f=view(canonical,labels.loc[labels.line.eq(line)].copy());all_views.append(f)
        path=OUT/f'counts_{line}.parquet';f.to_parquet(path,index=False);outputs[w.rel(path)]=w.sha(path)
        for year,g in f.groupby('year'):
            records.append({'line':line,'year':int(year),'rows':len(g),'accepted_events':int(g.n_accepted.sum()),'positive_events':int(g.n_positive.sum()),
                'positive_periods':int(g.positive_period.sum()),'accepted_without_positive_cost':int(g.accepted_without_positive_cost.sum()),
                'periods_multiple_accepted':int(g.n_accepted.gt(1).sum()),'T0_cents':int(g.T0_cents.sum())})
    whole=pd.concat(all_views,ignore_index=True);assert len(whole)==109296 and whole.row_id.is_unique
    assert whole.groupby('group_id').fold.nunique().max()==1
    check_sources(plan);dump(OUT/'report.json',{'author':'Codex','utc':utc(),'status':'P106existing_observed_counts_aligned_no_frequency_exposure_or_model',
        'records':records,'outputs':outputs,'rows':len(whole),'all_canonical_keys_cents_and_global_folds_preserved':True,
        'count_reporting_exposure_implemented':False,'paired_source_frequency_mark_views_exported':False,**plan['budget']})
    print(json.dumps({'count_views_prepared':True,'rows':len(whole),'accepted_events':int(whole.n_accepted.sum()),'positive_events':int(whole.n_positive.sum()),'positive_periods':int(whole.positive_period.sum()),'new_fits':0}))


def close():
    plan=w.read(PLAN);check_sources(plan);d=w.read(OUT/'report.json')
    assert all(w.sha(ROOT/path)==sha for path,sha in d['outputs'].items())
    next_unit='P107: design paired accepted-event count exposure for the new destination count path, using P27/P29definitions and current outer/inner group exclusions. Inspect existing source count-RKM support and q.cost_curves eligibility before implementing; count weights1must retain accepted cost0 events. Costweighted curves/caps cannot be silently reused as countCDF. Separate synthetic riskset/event enumeration and zero-exposure handling before any real CDFfit. Then registered historical P29frequency/mark export; no nativeFSpf-as-identified-frequency. No Poisson/cost model before complete paired-source/exposure recipe.'
    text='# P106: recuentos observados preparados\n\nCodex, '+utc()+'.\n\nSe reutilizaron las columnas de recuento del objetivo preparado; no se releyó o reasignó el inventario de siniestros. Las109296filas coinciden exactamente con las claves, año, grupos/folds, calendario y T0canónicos. Los céntimos coinciden por redondeo entero y Decimal. El coste objetivo permanece igual.\n\n'
    text+='| Ramo | Año | Filas | Eventos aceptados | Eventos con coste positivo | Periodos con coste positivo | Aceptados sin coste positivo |\n|---|---:|---:|---:|---:|---:|---:|\n'
    for z in d['records']:text+=f"|{z['line']}|{z['year']}|{z['rows']}|{z['accepted_events']}|{z['positive_events']}|{z['positive_periods']}|{z['accepted_without_positive_cost']}|\n"
    text+='\nUn periodo positivo no equivale a un evento: se conservan varios siniestros por periodo y los aceptados de coste0. Son recuentos reportados y aceptados a la valoración2024-12-31, no frecuencia última ni una instantánea de lo conocido al inicio de cada póliza. Pasaron los casos adversos de claves, importes y tipos, sin entrenar.\n\nLa exposición de número de avisos y las vistas explícitas de frecuencia/marca de fuente todavía no están conectadas a esta ruta. Se retomarán los contratos P27/P29; P61ya documentó que fFSpnativo usó completitud de costes, por lo que no se reinterpretará como frecuencia última. También se conservan los resultados adversos de credibilidad y fuente anteriores. Preparar los recuentos no demuestra un nuevo modelo o una mejora privada.\n\nLos aportes concurrentes revisados se trataron como evidencia, sin adoptar órdenes, sondas públicas, selección final o supuestos scores privados. Fuente, estado de siniestros/valoración, cola, transporte de mercado y búsqueda adaptativa siguen limitando la interpretación. Cero ajuste, CDF, inferencia, score o envío; B00 y alternativas preservados,2024abierto adaptativo, sin revisión profesional independiente.\n\nPróximo: '+next_unit+'\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),
        'outputs':d['outputs'],'count_reporting_exposure_implemented':False,'paired_source_frequency_mark_views_exported':False,
        **plan['budget'],'next_unit':next_unit,'2024_open':True,'goal_achieved':False,
        'forum':post(body,'COD-S2-20261027-PRIVADA-P106-RECUENTOS-RESULTADO','P106: recuentos enlazados, exposición de avisos aún pendiente')}
    cut=R/'privado'/('corte_P106_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));cut.mkdir();w.update(INDEX,receipt,cut)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P106'),(R/'registro/semana2_mision_privada_actual.json','P106')]:w.update(path,{key:receipt,'next_unit':next_unit},cut)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P106=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},cut)
    note='\n\n## Privada P106: recuentos observados\n\nCodex, '+receipt['utc']+'.109296filas canónicas enlazadas a recuentos existentes, coste/céntimos/grupos intactos; cero ajuste/score/inferencia/envíos. Exposición de número y vistas fuente pareadas todavía pendientes. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,cut)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_target_count_index':w.rel(INDEX),'week_2_private_target_count_report':w.rel(DOC)},cut)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['register','run','close'])
    {'register':register,'run':run,'close':close}[p.parse_args().mode]()
