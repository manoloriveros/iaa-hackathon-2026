"""Preflight del clima anual en la marca pareada, con frecuencia congelada."""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import copy
import json
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
sys.path.insert(0,str(R/'herramientas'))
import diagnosticar_numero_coste_P111 as previous
p=previous.p;k=p.k;m=k.p108.m;w=k.w;np=k.np;pd=k.pd
BASE=k.BASE;HOME=m.HOME;INNER=m.OUT
WEATHER=BASE/'P35_entradas_clima_20261026'
FIELDS=['annual_'+name for name in ['hail_days','wind_exposure_index','freezing_days','dry_summer_index','wildfire_index','rainfall_mm','mean_temperature_c']]
OUT=BASE/'P112_clima_marca_preflight_20261027'
PLAN=R/'registro/semana2_clima_marca_preflight_plan.json'
INDEX=R/'registro/semana2_clima_marca_preflight_actual.json'
DOC=R/'docs/semana2/PRIVADA_P112_CLIMA_EN_MARCA_PREFLIGHT.md'
dump=p.dump;utc=p.utc


def extend_preprocessor(weather,train,base):
    assert len(weather)==len(train) and np.asarray(train).dtype==bool
    own=weather.loc[train].copy()
    assert own.year.isin([2021,2022,2023,2024]).all()
    result=copy.deepcopy(base)
    assert not set(FIELDS).intersection(result['columns'])
    result['columns']=result['columns']+FIELDS
    for name in FIELDS:
        values=pd.to_numeric(own[name],errors='raise').to_numpy(float)
        assert len(values)>0 and np.isfinite(values).all()
        median=float(np.median(values));lo,hi=np.quantile(values,[.005,.995]);z=np.clip(values,lo,hi)
        scale=float(z.std());scale=scale if scale>1e-12 else 1.
        result['numeric'][name]={'median':median,'lo':float(lo),'hi':float(hi),'mean':float(z.mean()),'scale':scale}
    return result


def expanded(x,weather):
    assert len(x)==len(weather) and x.index.equals(weather.index) and not set(FIELDS).intersection(x)
    out=x.copy()
    for name in FIELDS:out[name]=pd.to_numeric(weather[name],errors='raise').to_numpy(float)
    return out


def mark_arguments(x,weather,labels,train,base):
    assert len(x)==len(weather)==len(labels)==len(train)
    assert x.index.equals(weather.index) and x.index.equals(labels.index)
    # Exclude held payload BEFORE parsing its labels, exposure or weather.
    own=labels.loc[train].copy()
    n=own.N.to_numpy(float);cost=own.C.to_numpy(float);en=own.EN.to_numpy(float);ec=own.EC.to_numpy(float)
    selected,ratio,y,weight=m.p27.transformed_mark(n,cost,en,ec)
    prep=extend_preprocessor(weather,train,base)
    features=expanded(x.loc[train].reset_index(drop=True),weather.loc[train].reset_index(drop=True))
    matrix,names=m.p14.transform(features,prep)
    alpha=float(n[selected].sum()/weight.sum())
    assert alpha>0
    return matrix[selected],y,weight,alpha,prep,names


def synthetic():
    rng=np.random.default_rng(20261027112);records=[];n=500;i=np.arange(n);train=i%5!=0
    for line in m.LINES:
        x=pd.DataFrame({'physical':rng.normal(0,1,n),'occupancy':np.where(i%2,'a','b')})
        x.loc[7,'physical']=np.nan
        weather=pd.DataFrame({'year':2021+i%4})
        for name in FIELDS:weather[name]=rng.uniform(0,1,n)
        count=rng.poisson(.7,n).astype(float);en=rng.uniform(.2,1,n);ratio=rng.uniform(.6,1.2,n)
        cost=count*ratio*np.exp(5+.3*weather[FIELDS[0]].to_numpy())*rng.lognormal(0,.2,n)
        cost[np.flatnonzero((count>0)&train)[0]]=0
        labels=pd.DataFrame({'N':count,'C':cost,'EN':en,'EC':en*ratio})
        base=m.p14.fit_preprocessor(x.loc[train]);base.pop('penalty',None)
        a=mark_arguments(x,weather,labels,train,base)
        bx=x.copy();bw=weather.copy();bl=labels.copy()
        for frame,names in [(bx,list(bx)),(bw,list(bw)),(bl,list(bl))]:
            for name in names:frame[name]=frame[name].astype('object');frame.loc[~train,name]='INVALID_HELD'
        b=mark_arguments(bx,bw,bl,train,base)
        assert np.array_equal(a[0].toarray(),b[0].toarray())
        assert all(np.array_equal(a[j],b[j]) for j in [1,2]) and a[3:]==b[3:]
        first,est=m.coefficients(a[0],a[1],a[2],'mark',a[3])
        folder=OUT/'synthetic'/line;folder.mkdir(parents=True)
        dump(folder/'primary_model.json',first)
        controls=m.controls(a[0],a[1],a[2],first,est,finite_difference=True)
        other,second_est=m.coefficients(b[0],b[1],b[2],'mark',b[3]);dump(folder/'adverse_model.json',other)
        assert first==other
        held=expanded(x.loc[~train].reset_index(drop=True),weather.loc[~train].reset_index(drop=True))
        matrix,names=m.p14.transform(held,a[4]);prediction=m.predict(matrix,first)
        loaded,n2=m.p14.transform(held,json.loads(json.dumps(a[4])))
        assert names==n2 and np.array_equal(prediction,m.predict(loaded,json.loads(json.dumps(other))))
        assert (a[1]==0).any()
        old,oldnames=m.p14.transform(x.loc[~train].reset_index(drop=True),base)
        indices=[names.index(name) for name in oldnames]
        assert np.array_equal(matrix[:,indices].toarray(),old.toarray())
        assert len(names)==len(oldnames)+7
        records.append({'line':line,'held_raw_feature_weather_label_exposure_poison_full_learning_exact':True,
            'old_feature_blocks_exact_no_relearning':True,'seven_climate_main_effects_only':True,
            'accepted_cost0_marks_retained':True,'JSONforward_exact':True,'controls':controls})
    return {'author':'Codex','utc':utc(),'records':records,'synthetic_primary_mark_GLM_fits':3,
        'synthetic_adverse_mark_GLM_fits_separate':3,'new_real_fits':0,'new_source_frequency_fits':0,'new_target_fits':0,'new_scores':0}


def register():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    assert w.read(previous.OUT/'completion_receipt.json')['report_sha256']==w.sha(previous.OUT/'report.json')
    paths=[Path(__file__),Path(m.__file__),Path(m.p14.__file__),Path(m.p14.old.__file__),Path(m.p27.__file__),
        previous.OUT/'report.json',previous.OUT/'completion_receipt.json',p.OUT/'report.json',INNER/'report.json',INNER/'completion_receipt.json',
        BASE/'P37_validacion_clima_20261026/report.json',R/'docs/semana2/PRIVADA_P37_VALIDACION_CLIMA_COMPLETA.md',
        WEATHER/'report.json',R/'registro/semana2_alcance_covariables_oficiales2025_v3.json']
    for line in m.LINES:
        paths += [HOME/f'matrix_s1_{line}.parquet',HOME/f'rows_s1_{line}.parquet',HOME/f'partition_source/folds_{line}.parquet',
            WEATHER/f'weather_s1_{line}.parquet',INNER/line/'preprocessor.json',INNER/line/'summary.json',INNER/line/'held_predictions.parquet',
            m.COUNTS/f'counts_{line}.parquet',m.LINKS/f'rkm_links_{line}.parquet']
    assert all(path.exists() for path in paths),[str(path) for path in paths if not path.exists()]
    OUT.mkdir()
    plan={'author':'Codex','utc':utc(),'scope':'Append seven same-calendar-year official climate main effects ONLY to the P28/P29source paired mark GLMs. Source frequency/count exposure and target P110count coefficients remain frozen. Preflight and own-source covariate bindings only now.',
        'need':'New P110/P111 show count estimates closer than cost and year-dependent reported mark mismatch; P29paired source preprocessors contain no weather field. This motivates a conditional-mark representation test, not a proven causal climate explanation.',
        'precedents':'E13/T7/T8and source-weather A1S P36/P37failed or lacked stable transfer. Preserve all. P37changed whole-cost A1Strees; this proposal changes ONLY source conditional marks under paired N/E_N/E_Ccontract, with fixed frequency and standard GLM main effects.',
        'configuration':{'fields':FIELDS,'base':'Exact original source-only P28preprocessor for held-source experiment, P29for later full-source stage. Existing feature blocks/statistics fixed; append seven train-only numeric .5-99.5clip/center/scale fields, no year/market/region IDs or selected interactions.',
            'mark_response':'P27exact selectedN>0,r=E_C/E_N>0; y=C/(N*r),w=N*sqrt(r), nominal alpha1 converted to sum(N)/sum(w). Accepted cost0 retained.',
            'estimator':m.EST,'frequency':'No source frequency or count CDF refit; reuse matching P28inner or P29full frequency coefficient/preprocessor objects, source count exposure unchanged.',
            'availability':'Official supplied same-year covariates, conditional retrospective contest prediction only. Not inception-known weather or a forecast. Reuse P35keys/ranges; do not repeat F05or2025file audit.',
            'prototype_boundary':'Select source train before parsing held raw feature/weather/N/C/EN/ECpayload. Fixed reporting objects still share source-held ancestors, as in original P28; this is conditional source validation, not full upstream invariance.'},
        'criterion':'3primary+3adverse synthetic actual markGLMs match after full held payload poison; objective/gradient/finite differences, exact original feature blocks and JSONpredictor. Three real source-only extended preprocessors/key bindings; no real GLMfit or target score now.',
        'future_source_stage':{'budget':'15source-held markGLMs,0newfrequency/CDF/targetfits. Later15fullsource markGLMs ONLYafter source veto pass and separate registration.',
            'source_veto':'Perline held whole cost sum(lambda_old*mark_new*E_C) deviance <=1.002times BOTH original P28paired aggregate and stored native tree context; same held rows/groups and source support>=100train/20held perperil. Gradient<=1e-4,no warnings and replay required. No perline model selection.',
            'invariance':'Actual source numeric design/y/w/alpha bindings must match under held payload corruption before real fit; synthetic3+3actualfits demonstrate deterministic full learner. Source-held CDFshared ancestry remains explicit.',
            'later_target':'If full source passes, update ONLY paired marks and their cost mixture with P110count models reused, then own T0levels refit. All original global/cohort/scenario/influence/level/transfer gates plus preregistered wildfire-range support reporting apply; no CSVfrom source alone.'},
        'sources':{w.rel(path):w.sha(path) for path in paths},'new_real_fits':0,'new_scores':0,'new2025inference':0,'new_submissions':0,
        'B00_all_alternatives_preserved':True,'2024_open':True,'goal_achieved':False}
    dump(PLAN,plan)
    body=OUT/'forum_previo.md';body.write_text('Codex. P112 registra antes del preflight una hipótesis acotada: añadir siete campos climáticos anuales oficiales SOLO al GLM de marca pareada por peril. Frecuencia, recuentos, exposiciones y preprocesamientos originales permanecen; se amplía el preprocesamiento con estadísticas climáticas del train fuente. El objetivo usa C/(N*r), peso N*sqrt(r), alpha nominal1 y coste0 aceptado. P110/P111 muestran desajuste de coste por evento variable por año, sin identificar clima como causa. E13/T7/T8/P36/P37 adversos siguen conservados: no se repite su modelo de coste o frecuencia. Solo 3+3 GLM sintéticos y tres enlaces fuente reales, sin ajuste real. Luego harían falta veto fuente, preinscripción completa y transferencia. El clima es información oficial condicional del concurso, no un pronóstico disponible al cotizar. La CDF fuente conserva ancestros compartidos: no se afirma independencia upstream. B00 intacto, privada prioritaria. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':'P112registered_before_conditional_mark_weather_preflight','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':k.p108.p107.previous.post(body,'COD-S2-20261027-PRIVADA-P112-CLIMA-MARCA-PREVIO','P112: clima en la marca pareada, frecuencia fija y sin promesa de mejora')}
    dump(OUT/'registration.json',receipt);dump(INDEX,receipt);print(json.dumps(receipt))


def run():
    plan=w.read(PLAN);p.m.check_sources(plan)
    with k.threadpool_limits(limits=2):dump(OUT/'synthetic.json',synthetic())
    report35=w.read(WEATHER/'report.json');records=[];outputs={}
    for line in m.LINES:
        rows=pd.read_parquet(HOME/f'rows_s1_{line}.parquet',columns=['row_id','year'])
        part=pd.read_parquet(HOME/f'partition_source/folds_{line}.parquet',columns=['row_id','source_group','internal_validation'])
        weather=pd.read_parquet(WEATHER/f'weather_s1_{line}.parquet')
        assert report35['outputs'][f'weather_s1_{line}.parquet']['sha256']==w.sha(WEATHER/f'weather_s1_{line}.parquet')
        assert all(np.array_equal(frame.row_id,rows.row_id) for frame in [part,weather])
        assert np.array_equal(weather.year,rows.year) and rows.year.isin([2021,2022,2023,2024]).all()
        train=~part.internal_validation.to_numpy(bool)
        assert set(part.loc[train,'source_group']).isdisjoint(set(part.loc[~train,'source_group']))
        base=w.read(INNER/line/'preprocessor.json');assert not any(name in base['columns'] for name in FIELDS)
        prep=extend_preprocessor(weather,train,base)
        bad=weather.copy()
        for name in ['year',*FIELDS]:bad[name]=bad[name].astype('object');bad.loc[~train,name]='INVALID_HELD'
        assert prep==extend_preprocessor(bad,train,base)
        source=pd.read_parquet(HOME/f'matrix_s1_{line}.parquet')
        sample=np.unique(np.linspace(0,len(rows)-1,64,dtype=int))
        xx=source.iloc[sample].reset_index(drop=True);ww=weather.iloc[sample].reset_index(drop=True)
        before,names=m.p14.transform(xx,base);after,newnames=m.p14.transform(expanded(xx,ww),prep)
        assert np.array_equal(before.toarray(),after[:,[newnames.index(name) for name in names]].toarray())
        assert len(newnames)==len(names)+7
        path=OUT/line/'preprocessor_inner.json';path.parent.mkdir();dump(path,prep);outputs[w.rel(path)]=w.sha(path)
        records.append({'line':line,'source_rows':len(rows),'training_rows':int(train.sum()),'held_rows':int((~train).sum()),
            'old_feature_blocks_sample_exact':True,'actual_weather_preprocess_held_poison_exact':True,
            'old_columns':len(names),'expanded_columns':len(newnames),'base_preprocessor_sha256':w.sha(INNER/line/'preprocessor.json')})
    p.m.check_sources(plan)
    dump(OUT/'report.json',{'author':'Codex','utc':utc(),'status':'P112conditional_mark_weather_synthetic_and_source_bindings_complete',
        'records':records,'outputs':outputs,'synthetic_primary_mark_fits':3,'synthetic_adverse_mark_fits_separate':3,
        'new_real_fits':0,'new_source_frequency_fits':0,'new_target_fits':0,'new_CDF_fits':0,'new_scores':0,'new2025inference':0,'new_submissions':0})
    print(json.dumps({'synthetic_complete':True,'source_bindings':3,'new_real_fits':0,'new_scores':0}))


def close():
    plan=w.read(PLAN);p.m.check_sources(plan);d=w.read(OUT/'report.json')
    assert all(w.sha(ROOT/path)==sha for path,sha in d['outputs'].items())
    next_unit='P113: implement/register15source-held markGLMs with exact P112extra7weatherfields and paired weights/alpha1. Retain P28frequency and basepreprocessors, source rows/groups and frozen reporting. Check actual poisoned-held numeric matrix/y/w/alpha arguments before fit, mark raw attempts, gradient/JSONreplay and BOTHsource vetoes<=1.002(P28paired, nativecontext) all3lines. No fullsource refit or target comparison until all source vetoes and separate registration pass; CDFshared source-held ancestry stays conditional.'
    text='# P112: clima anual solo en la marca, preflight\n\nCodex, '+utc()+'.\n\nPasaron tres GLM de marca sintéticos primarios y tres adversos. La alteración de covariables, clima, recuentos, importes y exposiciones retenidos antes del selector no cambió los argumentos ni los modelos aprendidos. Se conservaron marcas aceptadas de coste cero, el objetivo y gradiente se verificaron por otro método y los predictores coincidieron al recargar JSON.\n\nSe prepararon tres preprocesamientos fuente internos que añaden exactamente siete campos climáticos numéricos. Las estadísticas originales de variables físicas/categorías y sus bloques transformados no cambian; las nuevas estadísticas se estiman solo con grupos fuente de entrenamiento. Los tres cruces fuente reutilizan las claves y valores P35, sin repetir una descarga o auditoría del clima. No se ajustó ningún GLM real o modelo de frecuencia.\n\nLa hipótesis responde al nuevo contraste P110/P111 entre número y coste por evento. No prueba causalidad climática; los ensayos adversos previos de clima, incluido P37, se conservan. La evaluación fuente futura será condicional a CDF ya guardadas con ancestros compartidos, no una validación independiente de todo el reporte. El clima anual oficial se trata como covariable retrospectiva suministrada para el concurso, sin atribuir conocimiento previo a la cotización. No hay score o mejora privada nuevos, ni inferencia de 2025 o envío. B00 y alternativas intactos.\n\nPróximo: '+next_unit+'\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),
        'outputs':d['outputs'],'next_unit':next_unit,'new_real_fits':0,'new_scores':0,'new2025inference':0,'new_submissions':0,'2024_open':True,'goal_achieved':False,
        'forum':k.p108.p107.previous.post(body,'COD-S2-20261027-PRIVADA-P112-CLIMA-MARCA-RESULTADO','P112: marca con clima, controles sintéticos y fuentes enlazadas')}
    archive=R/'privado'/('corte_P112_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir();w.update(INDEX,receipt,archive)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P112'),(R/'registro/semana2_mision_privada_actual.json','P112')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    path=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(path)['week_2_mission017_phase2_20261025'];own.update(private_P112=receipt,next_unit=next_unit)
    w.update(path,{'week_2_mission017_phase2_20261025':own},archive)
    note='\n\n## Privada P112: clima en marca pareada\n\nCodex, '+receipt['utc']+'. Tres flujos sintéticos primarios/adversos y tres enlaces fuente pasaron, sin ajuste real o score. Frecuencia y bloques originales fijos, siete campos oficiales solo en marca. Informe '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_mark_weather_preflight_index':w.rel(INDEX),'week_2_private_mark_weather_preflight_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['register','run','close']);{'register':register,'run':run,'close':close}[parser.parse_args().mode]()
