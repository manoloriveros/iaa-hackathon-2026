"""Congela fuentes de pertenencia2023, JSON de C0 y código; evita tablas mixtas."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib
import json

ROOT=Path(__file__).resolve().parents[3]
REPO=ROOT/'Hackaton/Repositorio_IAA2026'
ID='S2-B20-PREFLIGHT-C02023-v1-20261024'
RUN=REPO/'privado/semana2/desarrollo2023/b20_preflight_c0_20261024_v1'
PLAN=REPO/'registro/semana2_b20_preflight_c0_plan_v1.json'
C0=REPO/'privado/semana2/ultimo/f0_ultimo_20261023T170841Z_82038766'
BASE=REPO/'privado/semana2/desarrollo2023/dev_20261023T173828Z_7efe46fc'
V8=REPO/'privado/semana2/desarrollo2023/dev8_20261024T013001Z_e8a35214'
B20=REPO/'privado/semana2/desarrollo2023/ridge20_20261024_v1'
PRODUCER=REPO/'src/semana2/preflight_c0_b20_2023.py'
SCOPE=REPO/'src/semana2/ambitos_c0_b20_2023.py'
PRE,RESULT='COD-S2-20261024-B20-C0-PRE','COD-S2-20261024-B20-C0-RESULT'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()


def dump(p,d):
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def main():
    assert not PLAN.exists() and not RUN.exists()
    files={}
    def add(p,expected=None):
        p=p.resolve(strict=True)
        assert p.is_relative_to(ROOT) and p.suffix in ['.json','.md','.py','.parquet']
        assert '2024' not in rel(p).lower() and 'test' not in rel(p).lower()
        digest=sha(p)
        if expected:assert digest==expected,'Fuente cambió: '+rel(p)
        files[rel(p)]=digest
    indices={}
    for label,name in [('design','semana2_b20_contraste_minimo_actual.json'),('support','semana2_b20_soporte_folds_actual.json')]:
        path=REPO/'registro'/name;add(path);indices[label]=rel(path);idx=read(path)
        add(ROOT/idx['plan'],idx['plan_sha256']);add(ROOT/idx['documentation'],idx['documentation_sha256'])
        for k in ['report','verification','terms','scope_graph','evidence_gaps','closure_verification']:
            if k in idx:add(ROOT/idx[k]['path'],idx[k]['sha256'])
    cm=read(C0/'manifest.json');bm=read(BASE/'manifest.json');rm=read(B20/'manifest.json')
    expected=lambda m,name:next(x['sha256'] for x in m['files'] if x['path']==name)
    for path in [C0/'manifest.json',BASE/'manifest.json',B20/'manifest.json']:add(path)
    add(C0/'code_snapshot.py',expected(cm,'code_snapshot.py'))
    add(REPO/'src/semana2/variables_ultimo.py',expected(cm,'code_snapshot.py'))
    add(B20/'code_snapshot.py',expected(rm,'code_snapshot.py'))
    add(BASE/'code_snapshot.py',expected(bm,'code_snapshot.py'))
    bplan=read(REPO/'registro/semana2_glm_ridge_coberturas_plan_v1.json')
    inputhash={x['path']:x['sha256'] for x in bplan['frozen_sources']}
    metadata_files={}
    for line in ['motor','buildings','contents']:
        path=V8/f'inputs_2023/{line}_fold0.parquet'
        add(path,inputhash[rel(path)]);metadata_files[line]=rel(path)
    scopes=[]
    for k in range(5):
        paths={}
        for name in ['reporting_fit_claims.parquet','severity_fit_weights.parquet','reporting_models.json','peril_cost_shares_buildings.json']:
            item=f'exclude_fold{k}/'+name;add(C0/item,expected(cm,item));paths[name]=rel(C0/item)
        link=BASE/f'links_2023/buildings_fold{k}.parquet';add(link,expected(bm,f'links_2023/buildings_fold{k}.parquet'))
        cached=V8/f'inputs_2023/buildings_fold{k}.parquet';add(cached,inputhash[rel(cached)])
        receipt=B20/f'models/buildings_fold{k}/receipt.json';add(receipt,expected(rm,f'models/buildings_fold{k}/receipt.json'))
        paths.update(link_2023=rel(link),B20_input_2023=rel(cached),B20_receipt=rel(receipt))
        scopes.append({'outer_fold':k,'files':paths})
    for name in ['semana2_contrato_entrenamiento.json','semana2_glm_ridge_coberturas_plan_v1.json',
        'semana2_contadores_propios_actual.json','semana2_desarrollo2023_actual.json','semana2_glm_ridge_actual.json','semana2_politica_seleccion_v1.json']:
        add(REPO/'registro'/name)
    for path in [PRODUCER,SCOPE]:add(path)
    RUN.mkdir();(RUN/'sources').mkdir();frozen=[]
    for i,(path,digest) in enumerate(files.items()):
        snap=RUN/'sources'/f'{i:02d}_{Path(path).name}';snap.write_bytes((ROOT/path).read_bytes());assert sha(snap)==digest
        frozen.append({'path':path,'sha256':digest,'snapshot':rel(snap)})
    p={'id':ID,'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'path_base':'workspace_root',
       'authorization_literal':'Continúa con el preflight del contraste mínimo de B20: audita las dependencias de C0 y el aislamiento entre folds. Registra qué falta y mantén el soporte como fallido, sin reentrenar ni abrir 2024 o test.',
       'indices':indices,'frozen_sources':frozen,'outer_scopes':scopes,'period_metadata_files':metadata_files,
       'C0_code':rel(C0/'code_snapshot.py'),'scope_module':rel(SCOPE),'scope_module_sha256':sha(SCOPE),
       'producer':rel(PRODUCER),'producer_sha256':sha(PRODUCER),'output_run':rel(RUN),
       'scope':'Read only existing2023 metadata, scoped2023 C0 fit artifacts, 2023-only links/caches and source code. Parent manifests are hash/path metadata only. Never open mixed-year observation tables, rawdata, summaries with2024 rows, model bundles, 2024/test/actas/ledger.',
       'method':['Read unique period/group/customer/address/year/test membership from three saved2023 B20 input caches, metadata columns only',
           'Reconcile five C0 training-claim scopes and saved weights/parameters with retained-fold exclusion',
           'Match five2023C0 links with B20cached inputs; inspect receipts/source without fitting',
           'Enumerate ten planned threefold memberships and twenty ordered nested scopes; prove unsafe cache reuse by actual membership',
           'Audit all C0 ancestors and count prospective per-peril work without estimating values',
           'Exercise metadata-only scope selector on adversarial fixtures; no claim of poisoning a fitted C0'],
       'building_perils':['accidental_damage','escape_of_water','fire','flood','storm','subsidence'],
       'frozen_target_convention':'T0 and historical fixed valuation2024-12-31 unchanged; valuation date is not a policy2024 validation opening.',
       'parameter_namespace':{'reserve_rho':1.0,'calibration_beta':'unestimated proposed[0,1]; never passed as reserve rho'},
       'read_columns_policy':'No loss values needed for membership. Read metadata plus storedC0 exposure and existingweights/parameterJSON; no T0/reserve labels from parquet or new predictions.',
       'support_gate':'failed','thresholds_relaxed':False,'claims_or_groups_excluded':0,'fit_authorized':False,'can_execute':False,
       'new_fits':0,'new_inference':0,'new_C0_values':0,'parameters_estimated':0,'new_bootstrap':0,
       'reference':'W2-B00','promotion':False,'all_alternatives_preserved':True,'2024_test_closed':True,'ledger_read':False,
       'prior_external2024_header_exposure_disclosed':True,'complete_blindness_claim_allowed':False,
       'professional_independent_validation':False,'forum_prior':PRE,'forum_result':RESULT,
       'acceptance':'Source hashes exact, existing metadata scopes reconciled, every protection checked, unsafe/reused/missing inner artifacts labeled unfit. Passing preflight checks never clears failed support or authorizes training.'}
    dump(PLAN,p);dump(RUN/'plan_snapshot.json',p)
    npath=REPO/'registro/semana2_continuidad_nocturna.json';n=read(npath)
    unit={'id':ID,'plan':rel(PLAN),'status':'preregistered_metadata_only_C0_preflight','forum_prior':PRE}
    if n.get('current_unit'):n.setdefault('parallel_artifact_diagnostics',{})[ID]=unit
    else:n['current_unit']=unit
    dump(npath,n)
    (REPO/'registro'/(PRE+'_cuerpo.md')).write_text(
        'Preflight autorizado del contraste B20, plan '+ID+'. Soporte continúa FALLIDO y sin permiso operativo para ajustar. '
        'Se auditan ámbitos de cinco C0 exteriores, metadata2023 de periodos/siniestros, pesos y parámetros guardados, vínculos2023/caches y código; '
        'sin tablasmixtas, originales, modelosserializados, prediccionesnuevas, T0/reservasdeParquet, entrenamiento o cálculo de C0nuevo. '
        'Se enumeran diez tríos yveinte scopes internos como pertenencias hipotéticas y se prueban reutilizaciones incompatibles. '
        'Curvas, marcas, frecuencias/denominadores y mezcla C0 deben compartir ámbito. rho_reservas1 se separa de beta_calibración no estimada. '
        'Se conserva objetivo/cortehistórico, B00/B01–B20, contadores, umbrales, todoslossiniestros y 2024/test/actas/SEL01/ledgercerrados. '
        'Pruebas de selector metadatos no equivalen a validación numérica del C0 aún no implementado. Exposiciónprevia de títuloajeno declarada sinuso/ceguera completa.\n',encoding='utf-8')
    print(json.dumps({'id':ID,'sources':len(frozen),'support_gate':'failed','new_fits':0}))


if __name__=='__main__':main()
