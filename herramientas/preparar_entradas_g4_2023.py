"""Materializa entradas heredadas2023 y ámbitos lógicos; nunca ajusta objetos."""
from pathlib import Path
from datetime import datetime,timezone
from contextlib import ExitStack
from unittest.mock import patch
import json,hashlib,sys,traceback,socket,pickle
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(REPO/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'));sys.path.insert(0,str(REPO/'herramientas'))
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import joblib
from sklearn.linear_model import TweedieRegressor
from sklearn.pipeline import Pipeline
from semana2 import entradas_g4_2023 as core,c0_estricto2023
from probar_adaptador_entradas_g4_2023 import verify
PLAN=REPO/'registro/semana2_g4_entradas2023_plan_v1.json'
RUN=REPO/'privado/semana2/entradas_g4_2023/ingreso_20261024_v1'
rel=lambda p:p.relative_to(ROOT).as_posix()
now=lambda:datetime.now(timezone.utc).isoformat()

def dump(p,o):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8') as f:json.dump(o,f,ensure_ascii=False,indent=2);f.write('\n')

def main():
    plan=json.loads(PLAN.read_text(encoding='utf-8'))
    forum=(ROOT/'Hackaton/Semana 2/Foro/FORO.md').read_bytes();assert forum.count(('<!-- aporte:'+plan['forum_prior']+' -->').encode())==1
    for x in plan['frozen_code']:assert core.sha(ROOT/x['path'])==x['sha256'],x['path']
    attempt=1
    while (RUN/f'attempt{attempt}').exists():attempt+=1
    out=RUN/f'attempt{attempt}';out.mkdir()
    for x in plan['frozen_code']:(out/Path(x['path']).name).write_bytes((ROOT/x['path']).read_bytes())
    allowed={str(core.safe_path(ROOT,s['path'])) for s in plan['sources'].values()};read_table=pq.read_table
    events=[];forbidden=[]
    def no_fit(*a,**kw):forbidden.append('fit_or_model_load');raise AssertionError('No fits or model loads in ingress')
    def no_network(*a,**kw):forbidden.append('network');raise AssertionError('No network in ingress')
    def checked_read(path,*a,**kw):
        p=Path(path).resolve();assert str(p) in allowed or p.is_relative_to(out),'Unlisted input reader'
        cols=kw.get('columns');assert cols is not None,'Explicit column whitelist required'
        assert not any(c.startswith(('e_cost','q_cost','prediction','annual_rate','unit_deviance')) or c in ['C0','x_log_sum_insured'] for c in cols),'Scoped learned/C0 column prohibited'
        events.append({'path':rel(p),'columns':list(cols)});return read_table(path,*a,**kw)
    try:
        with ExitStack() as stack:
            for obj,name in [(TweedieRegressor,'fit'),(Pipeline,'fit'),(c0_estricto2023,'fit_c0_2023'),(joblib,'load'),(pickle,'load')]:stack.enter_context(patch.object(obj,name,no_fit))
            stack.enter_context(patch.object(socket.socket,'connect',no_network));stack.enter_context(patch.object(pq,'read_table',checked_read))
            inputs={};proof=[];core.READS.clear()
            for name,spec in plan['sources'].items():
                inputs[name],receipt=core.read_pinned(ROOT,spec);proof.append({'source':name,**receipt})
            frames=core.build_frames(inputs)
            def write(name,frame,fold=None):
                path=out/(name+'.parquet');path.parent.mkdir(parents=True,exist_ok=True);assert not path.exists()
                pq.write_table(pa.Table.from_pandas(frame,preserve_index=False),path)
                spec={'path':rel(path),'sha256':core.sha(path),'columns':list(frame.columns),'kind':'prepared'}
                core.footer_proof(path,spec['columns'],expected_fold=fold);return spec
            meta=write('memberships_2023',frames['metadata']);foldfiles={}
            for fold in range(5):
                foldfiles[str(fold)]={name:write(name+'/fold_'+str(fold),frames[name][frames[name].fold.eq(fold)].copy(),fold)
                    for name in ['periods','targets','claims','capital_audit']}
            excluded=out/'excluded_claim_audit_2023.parquet'
            pq.write_table(pa.Table.from_pandas(frames['excluded_claim_audit'],preserve_index=False),excluded)
            scopes=core.make_scopes(frames['metadata'],foldfiles)
            manifest={'id':plan['id'],'author':'Codex','utc':now(),'market':'emerging','cohort':2023,'metadata':meta,'fold_files':foldfiles,'scopes':scopes,
                'global_membership_sha256':core.validate_membership(frames['metadata']),'source_versions':plan['sources'],
                'capital_rule':'CAPS2-01 scope-specific parameters required; no parameters estimated here. Premium retained audit-only in separate table.',
                'C0_present':False,'model_input_ready':False,'fixture_id_added':False,'no_synthetic_relabeling':True}
            dump(out/'input_manifest.json',manifest)
            validation=verify(ROOT,out/'adapter_contract_tests',manifest)
        assert not forbidden
        dump(out/'source_footer_proofs.json',{'id':plan['id'],'proofs':proof,'no_multiyear_decoder_used':True})
        dump(out/'reader_events.json',{'events':events,'pinned_reads':core.READS,'forbidden_calls':forbidden})
        dump(out/'validation.json',validation)
        counts={k:len(v) for k,v in frames.items()}
        result={'id':plan['id'],'author':'Codex','utc':now(),'attempt':attempt,'success':True,'out':rel(out),'counts':counts,'scopes':15,
            'new_models':0,'new_C0_fits':0,'new_predictions':0,'new_scores':0,'learned_capital_parameters':0,
            'model_input_ready':False,'C0_present':False,'scope':'Prepared2023 base inputs,labels and logical scopes only. Not a fitting authorization or a new information source.'}
        dump(out/'result.json',result);dump(RUN/'prepared_current.json',result)
        print(json.dumps(result,ensure_ascii=True));return 0
    except Exception as exc:
        dump(out/'failure.json',{'id':plan['id'],'utc':now(),'exception':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc(),'reader_events':events,'forbidden_calls':forbidden})
        print(json.dumps({'success':False,'attempt':attempt,'exception':type(exc).__name__,'message':str(exc),'failure':rel(out/'failure.json')},ensure_ascii=True));return 1

if __name__=='__main__':raise SystemExit(main())
