"""Congela la auditoría de soporte guardado; no estima ni infiere modelos."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT/'Hackaton/Repositorio_IAA2026'
ID = 'S2-B20-SOPORTE-FOLDS2023-v1-20261024'
RUN = REPO/'privado/semana2/desarrollo2023/b20_soporte_folds_20261024_v1'
PLAN = REPO/'registro/semana2_b20_soporte_folds_plan_v1.json'
PRODUCER = REPO/'src/semana2/auditar_soporte_b20_folds2023.py'
PRE, RESULT = 'COD-S2-20261024-B20-SUPPORT-PRE', 'COD-S2-20261024-B20-SUPPORT-RESULT'
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: p.relative_to(ROOT).as_posix()


def dump(p,d):
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def main():
    assert not PLAN.exists() and not RUN.exists()
    files = {}

    def add(p, expected=None):
        p = p.resolve(strict=True)
        assert p.is_relative_to(ROOT) and '2024' not in rel(p).lower() and 'test' not in rel(p).lower()
        assert p.suffix in ['.json','.md','.py','.parquet']
        digest = sha(p)
        if expected:
            assert digest == expected, 'Fuente cambiada: '+rel(p)
        files[rel(p)] = digest

    indices = {}
    for label,name in [('design','semana2_b20_contraste_minimo_actual.json'),
                       ('bands','semana2_b20_bandas_calibracion_actual.json')]:
        path = REPO/'registro'/name
        add(path)
        indices[label] = rel(path)
        d = read(path)
        add(ROOT/d['plan'],d['plan_sha256'])
        add(ROOT/d['documentation'],d.get('documentation_sha256'))
        for key in ['report','verification','manifest','readout','terms','readiness','closure_verification']:
            if key in d:
                add(ROOT/d[key]['path'],d[key]['sha256'])
    bi = read(ROOT/indices['bands'])
    bandrun = ROOT/bi['run']
    manifest = read(ROOT/bi['manifest']['path'])
    artifacts = {}
    for name in ['calibration_cells_2023.parquet','heldout_bands_2023.parquet',
                 'training_rate_replays_2023.parquet','band_cuts.json']:
        item = next(x for x in manifest['files'] if x['path']==name)
        add(bandrun/name,item['sha256'])
        artifacts[name] = rel(bandrun/name)
    for name in ['semana2_contadores_propios_actual.json','semana2_desarrollo2023_actual.json',
                 'semana2_glm_ridge_actual.json','semana2_politica_seleccion_v1.json']:
        add(REPO/'registro'/name)
    add(PRODUCER)
    RUN.mkdir()
    (RUN/'sources').mkdir()
    frozen = []
    for i,(path,digest) in enumerate(files.items()):
        snap = RUN/'sources'/f'{i:02d}_{Path(path).name}'
        snap.write_bytes((ROOT/path).read_bytes())
        assert sha(snap)==digest
        frozen.append({'path':path,'sha256':digest,'snapshot':rel(snap)})
    design = read(ROOT/read(ROOT/indices['design'])['plan'])
    plan = {'id':ID,'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'path_base':'workspace_root',
        'authorization_literal':'Continúa con la auditoría del soporte de B20 por fold usando artefactos guardados. Registra qué falla y qué evidencia falta, sin relajar umbrales, excluir siniestros, reentrenar ni abrir 2024 o test.',
        'hypothesis':'The failed pooled screen can conceal distinct fold-level support breaches. Audit each retained cell under unchanged design thresholds; no new model evidence is assumed.',
        'indices':indices,'artifacts':artifacts,'frozen_sources':frozen,
        'producer':rel(PRODUCER),'producer_sha256':sha(PRODUCER),'output_run':rel(RUN),
        'gate':{'line':'buildings','heldout_bands':[1,5],'folds':[0,1,2,3,4],
                'fold_tail':design['support']['fold_tail'],'pooled_tail':design['support']['pooled_tail'],
                'inner_calibration_each_outer_scope':design['support']['inner_calibration_each_outer_scope'],
                'all_conditions_conjunctive':True,'unknown_blocks':True,'no_rounding_before_verdict':True},
        'method':'Classify savedB20 heldout cell stats, no rebins. Independently reconcile only audit-related support/group quantities from saved heldout rows using cents/dictionaries, without rerunning calibration or model suites.',
        'inventory':'75 heldout line-fold-band cells and15pooledline-band cells. Only10buildingtailcells+2pooledtails are eligibility gates; othercells descriptive.',
        'outer_fit_proxy':'Read saved buildings fit replay and cuts for five original4/5fit scopes. Count distinctpositivegroups overwhole scope, report originalP20/P80 lograte span and tailstats. These in-sample savedrates do not establish required nested inner-OOF support; no pass claim for innergate.',
        'missing_evidence':['Actual inner-OOF rates/C0 excluding both outer and inner folds',
            'Inner-scope support and lograte spread','Strict2023 scoped implementation and first-stage resource enumeration',
            'Evidence of mechanism stability/validated benefit; no new parameters or metrics here',
            'Separate training scope authorization; current gate remains failed if any breach'],
        'guard':'Only hashed saved2023 artifact allowlist. No originaldata, OOF prediction generation, model loads, fit, changed bands, group/claim deletion, normalization, bootstrap, score or modelselection.',
        'resources':{'new_fits':0,'new_inference':0,'new_bootstrap':0,'parameters_estimated':0,'new_recipes':0},
        '2024_test_closed':True,'ledger_read':False,'promotion':False,'reference':'W2-B00',
        'all_alternatives_preserved':True,'prior_external2024_header_exposure_disclosed':True,
        'complete_blindness_claim_allowed':False,'professional_independent_validation':False,
        'forum_prior':PRE,'forum_result':RESULT,
        'IAA':'Documentation2-3, Governance2.8, ProfessionalConsiderations3.1/3.3; ownreview, no independent certification.'}
    dump(PLAN,plan)
    dump(RUN/'plan_snapshot.json',plan)
    npath=REPO/'registro/semana2_continuidad_nocturna.json'
    n=read(npath)
    unit={'id':ID,'plan':rel(PLAN),'status':'preregistered_saved_fold_support_audit','forum_prior':PRE}
    if n.get('current_unit'):
        n.setdefault('parallel_artifact_diagnostics',{})[ID]=unit
    else:
        n['current_unit']=unit
    dump(npath,n)
    (REPO/'registro'/(PRE+'_cuerpo.md')).write_text(
        'Auditoría autorizada del soporte porfold B20 con artefactos guardados. Plan '+ID+' congelado antes del análisis. '
        'Se aplican exactamente las reglas del diseño previo a las diez celdas retenidas edificios bandas1/5 y doscolas agrupadas. '
        'Se inventarían las75celdas ramo/fold/banda, sin extender umbrales de edificios a otrosramos o bandas. '
        'El ajuste exterior4/5 guardado solo será contexto para positivos/rango y colas, nunca evidencia de soporte internoOOF. '
        'Fuentes con SHA y snapshots; lectura selectiva de celdas/tasas guardadas, sin modelo/inferencia/fit/remuestreo/precio nuevo. '
        'No rebinning, relajación de umbrales, exclusión de siniestros/componentes o cambio deT0/C0. '
        '2024/test/actas/scores/SEL01/ledger cerrados, B00/B01–B20 y contadores intactos; exposición previa ajena declarada sinuso/ceguera completa.\n',encoding='utf-8')
    print(json.dumps({'id':ID,'sources':len(frozen),'new_fits':0}))


if __name__=='__main__':
    main()
