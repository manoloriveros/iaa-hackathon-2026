"""Completa solo conciliación/cierre tras registro ya hecho; no repite cálculos."""
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import unquote
import hashlib,json,os,re,sys
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
RUN=REPO/'privado/semana2/desarrollo2023/contraccion_b20_20261024T023428Z_7f3565db'
INDEX=REPO/'registro/semana2_b20_contraccion_actual.json';NIGHT=REPO/'registro/semana2_continuidad_nocturna.json'
STATEKEY='week_2_B20_contraction2023_v2_20261024';NOW=datetime.now(timezone.utc).isoformat()
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pyarrow.parquet as pq
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()


def dump(path,obj):
    with path.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')


def top(raw,key,value):
    val=json.dumps(value,ensure_ascii=False,indent=2).replace('\n','\n  ');m=re.search(r'(?m)^  '+re.escape(json.dumps(key))+r':\s*',raw);assert m,key
    _,end=json.JSONDecoder().raw_decode(raw[m.end():]);return raw[:m.end()]+val+raw[m.end()+end:]


def main():
    p=read(RUN/'plan_snapshot.json');i=read(INDEX);registration=read(RUN/'registration.json')
    assert all(sha(ROOT/x['path'])==x['sha256'] for x in p['frozen_sources'])
    n=read(NIGHT);entry=[x for x in n['completed_units'] if x['id']=='S2-B20-ATRIBUCION2023-v1a-20261024'];assert len(entry)==1
    foreign=ROOT/entry[0]['run'];ref=entry[0]['verification'];assert sha(ROOT/ref['path'])==ref['sha256'] and read(ROOT/ref['path'])['failed']==0
    own=pq.read_table(RUN/'fixed_period_logratio_decomposition.parquet').to_pandas().sort_values(['market','line','row_id']).reset_index(drop=True)
    source=foreign/'log_rate_change_components.parquet'
    other=pq.read_table(source,filters=[('row_id','in',own.row_id.tolist())]).to_pandas().sort_values(['market','line','row_id']).reset_index(drop=True)
    pairs={'delta_intercept':'log_intercept','delta_coverage':'log_coverage','delta_newbusiness':'log_business','delta_other_main_effects':'log_other','delta_log_rate':'log_change'}
    assert len(own)==len(other)==20 and own[['market','line','row_id']].equals(other[['market','line','row_id']])
    errors={a:float(np.abs(own[a]-other[b]).max()) for a,b in pairs.items()};assert all(x<2e-12 for x in errors.values())
    reconciliation={'author':'Codex','utc':NOW,'concurrent_completed_id':entry[0]['id'],'concurrent_run':entry[0]['run'],'verification_receipt':ref,
                    'source_log':{'path':rel(source),'sha256':sha(source)},'own_log':{'path':rel(RUN/'fixed_period_logratio_decomposition.parquet'),'sha256':sha(RUN/'fixed_period_logratio_decomposition.parquet')},
                    'checked_fixed_rows':20,'max_absolute_term_errors':errors,'passed':True,'source_not_available_at_initial_v2_cut_but_reconciled_after_completion':True,
                    'full_attribution_suite_or_training_repeated':False,'professional_independent_validation':False}
    dump(RUN/'concurrent_v1a_reconciliation.json',reconciliation)
    nextstep='Consolidate the existing2023 risk matrix for B00/B12/B14/B19/B20 by line/business, level, uncertainty and influence using completed receipts. Both B20 attributionv1a and contractionv2 are reconciled; do not rerun either suite, resampling or fitting. Keep B00/all alternatives, unresolved ultimate/reporting/capital warnings and own2024/test closed.'
    backup=RUN/'state_before_closure_reconciliation';backup.mkdir();changes=[]
    def change(path,fn):
        before=path.read_bytes();b=backup/path.relative_to(ROOT);b.parent.mkdir(parents=True,exist_ok=True);b.write_bytes(before)
        after=fn(before.decode('utf-8-sig')).encode('utf-8')
        if before.startswith(b'\xef\xbb\xbf'):after=b'\xef\xbb\xbf'+after
        temp=path.with_name(path.name+'.b20final.tmp');assert path.read_bytes()==before
        with temp.open('xb') as f:f.write(after);f.flush();os.fsync(f.fileno())
        assert path.read_bytes()==before;os.replace(temp,path)
        changes.append({'path':rel(path),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':sha(path),'backup':rel(b)})
    note='\n\n## Conciliación de cierre con atribución B20 v1a\n\nCodex, corte UTC '+NOW+'. La atribución concurrente había terminado como v1a en otro directorio, sin cambiar el modo focal fijado antes del cálculo. Sus veinte términos de los mismos periodos concilian con este diagnóstico dentro de 2e-12. Se leyó su recibo corregido por SHA y se cotejó solo el subconjunto; no se repitieron sus pruebas o atribución global. La concordancia entre cálculos de Codex no es revisión profesional independiente.\n\nEl primer control de cierre asumía que v2 seguía en una entrada paralela; la continuidad real y el recibo de preparación muestran que pasó al carril principal al concluir la otra unidad. Falló esa comprobación después de registrar correctamente los resultados. Se conserva el fallo y se completa solo el cierre según el modo real, sin repetir registro, cálculos, modelos o verificaciones estadísticas. Ambas unidades quedan terminadas, B00 y alternativas conservados, 2024/test cerrados. Próximo paso: consolidar una matriz de riesgos por ramo/negocio con los recibos existentes, sin otra tanda.\n'
    change(ROOT/i['documentation'],lambda raw:raw+note)
    i.update(documentation_sha256=sha(ROOT/i['documentation']),next_artifact_diagnostic=nextstep,
             concurrent_v1a_reconciliation={'path':rel(RUN/'concurrent_v1a_reconciliation.json'),'sha256':sha(RUN/'concurrent_v1a_reconciliation.json')},
             closing_mode_correction='Actual current-unit completion, not assumed parallel entry; no registration mutations replayed')
    change(INDEX,lambda raw:json.dumps(i,ensure_ascii=False,indent=2)+'\n')
    def night(raw):
        obj=json.loads(raw);obj['latest_B20_concurrent_reconciliation']=i['concurrent_v1a_reconciliation'];obj['next_artifact_diagnostic']=nextstep
        if obj.get('current_unit') is None:obj['next_unit']=nextstep
        obj['updated_utc']=NOW;return json.dumps(obj,ensure_ascii=False,indent=2)+'\n'
    change(NIGHT,night)
    def state(raw):
        obj=json.loads(raw);dev=dict(obj[STATEKEY],concurrent_v1a_reconciliation=i['concurrent_v1a_reconciliation'],closing_mode_correction=i['closing_mode_correction'],next_artifact_diagnostic=nextstep,documentation_sha256=i['documentation_sha256'])
        continuity=dict(obj['week_2_nocturnal_continuation_20261023'],as_of_utc=NOW,next_artifact_diagnostic=nextstep)
        return top(top(raw,STATEKEY,dev),'week_2_nocturnal_continuation_20261023',continuity)
    change(ROOT/'Preparación/ESTADO_PROYECTO.json',state)
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:change(ROOT/'Preparación'/name,lambda raw:raw+note)
    for name in ['PLAN_NOCTURNO_20261023.md','BALANCE_NOCTURNO_PARCIAL_20261024.md']:
        change(REPO/'docs/semana2'/name,lambda raw:raw+'\n\nLa atribución B20 v1a ya terminó y sus veinte términos concilian con la [contracción focal](CONTRACCION_Y_NIVEL_B20_VS_B19_2023.md), sin repetir su suite. Ambas unidades quedan conciliadas; siguiente trabajo, consolidar matriz de riesgos de 2023 con recibos existentes. B00/alternativas conservados y 2024 cerrado.\n')
    change(REPO/'registro/semana2_listo_entrenar.json',lambda raw:top(raw,'latest_B20_saved_coefficient_level_diagnostic',dict(json.loads(raw)['latest_B20_saved_coefficient_level_diagnostic'],next_artifact_diagnostic=nextstep,concurrent_v1a_reconciled=True)))
    dump(RUN/'registration_continuation.json',{'author':'Codex','utc':NOW,'changes':changes,'closing_only':True,'successful_fit_calls':0,'no_statistical_suite_repeated':True})
    checks=[]
    def check(name,ok):checks.append({'name':name,'pass':bool(ok)})
    for key in ['report','verification','readout','readout_reconciliation','assessment','decision_journal','manifest','incident_check','focused_interpretation_receipt','preregistration_completion_receipt','concurrent_v1a_reconciliation']:
        check('Index receipt '+key,sha(ROOT/i[key]['path'])==i[key]['sha256'])
    check('Documentation final exact',sha(ROOT/i['documentation'])==i['documentation_sha256'])
    for x in p['frozen_sources']:check('Frozen source '+x['path'],sha(ROOT/x['path'])==x['sha256'])
    for x in read(RUN/'manifest.json')['files']:check('Producer artifact '+x['path'],sha(ROOT/x['path'])==x['sha256'])
    allchanges=registration['changes']+changes
    for x in allchanges:
        if x['path'].endswith('.md'):check('Prose prefix '+x['path']+x['backup'],(ROOT/x['path']).read_bytes().startswith((ROOT/x['backup']).read_bytes()))
    untouched=registration['unrelated_indices_and_counters_cut'];check('No active catalog/counter written',not set(untouched).intersection(x['path'] for x in allchanges))
    pointerchanges={path:{'before':before,'now':sha(ROOT/path)} for path,before in untouched.items() if sha(ROOT/path)!=before}
    first=RUN/'state_before_registration';oldstate=read(first/'Preparación/ESTADO_PROYECTO.json');state=read(ROOT/'Preparación/ESTADO_PROYECTO.json')
    allowed={'current_phase','memory_as_of','week_2_nocturnal_continuation_20261023','collaboration_forum'}
    check('Old state branches preserved',all(state.get(k)==val for k,val in oldstate.items() if k not in allowed))
    oldroutes=read(first/'RUTAS_PROYECTO.json');routes=read(ROOT/'RUTAS_PROYECTO.json');check('Earlier routes preserved',all(routes.get(k)==val for k,val in oldroutes.items()))
    for key in ['week_2_b20_contraction_index','week_2_b20_contraction_report','week_2_b20_contraction_plan']:check('New route '+key,(ROOT/routes[key]).exists())
    for path in [ROOT/i['documentation'],REPO/'docs/semana2/PLAN_NOCTURNO_20261023.md',REPO/'docs/semana2/BALANCE_NOCTURNO_PARCIAL_20261024.md',ROOT/'Hackaton/Semana 2/README.md',ROOT/'Hackaton/Semana 2/PLAN_TRABAJO.md']:
        for link in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8-sig')):
            target=link.strip('<>').split('#')[0]
            if not target or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://',target):continue
            check('Local link '+rel(path)+' -> '+target,(path.parent/unquote(target)).resolve().exists())
    newn=read(NIGHT);oldn=read(first/NIGHT.relative_to(ROOT))
    check('Own unit completed exactly once',sum(x['id']==p['id'] for x in newn['completed_units'])==1)
    check('Earlier completed units exact',newn['completed_units'][:len(oldn['completed_units'])]==oldn['completed_units'])
    check('Actual current-unit mode completed',(oldn.get('current_unit') or {}).get('id')==p['id'] and newn['current_unit'] is None)
    check('Superseded draft not completed',not any(x['id']=='S2-B20-CONTRACCION2023-v1-20261024' for x in newn['completed_units']))
    for key in ['window_start','window_end','frequency','automation_id','automation_kind','automation_target_thread','same_chat','other_automations_changed','forum_reading_guard','confirmation_header_exposure']:check('Schedule/guard exact '+key,newn[key]==oldn[key])
    check('Warnings retained',all(x in newn['open_conditions'] for x in oldn['open_conditions']))
    check('Own2024closed',newn['confirmation_2024_open'] is False and state[STATEKEY]['ledger_read'] is False)
    forum=ROOT/'Hackaton/Semana 2/Foro/FORO.md';data=forum.read_bytes();target='49c95743022861ca708f05815990304d42a4178a8b0edfc57178bb8e704ee668';digest=hashlib.sha256();prefix_found=False
    for line in data.splitlines(keepends=True):
        digest.update(line)
        if digest.hexdigest()==target:prefix_found=True;break
    check('Serialized forum042 prefix intact',prefix_found)
    for suffix in ['040','041','042']:check('Forum own ID once '+suffix,data.count(('<!-- aporte:COD-S2-20261024-'+suffix+' -->').encode())==1)
    for path in read(RUN/'verification.json')['expected_failure_runs']:check('Actual CLI expected failure archived',(ROOT/path/'expected_adversary_failure.json').exists())
    receipt={'utc':NOW,'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks,'concurrent_pointer_changes':pointerchanges,
             'closing_assertion_corrected_for_actual_current_mode':True,'no_registration_or_statistical_suite_replayed':True}
    dump(RUN/'closure_verification.json',receipt);assert receipt['failed']==0,[x for x in checks if not x['pass']]
    paths={x for x in RUN.rglob('*') if x.is_file()};paths.update(ROOT/x['path'] for x in allchanges)
    paths.update([INDEX,ROOT/i['documentation'],ROOT/i['plan'],ROOT/p['code'],Path(__file__),forum,REPO/'registro/semana2_b20_contraccion2023_pruebas_v2.json'])
    paths.update(REPO/'herramientas'/name for name in ['verificar_contraccion_b20_2023.py','documentar_contraccion_b20_2023.py'])
    for pattern in ['*contraccion*b20*.py','*contraccion*b20*.json','contraccion_b20*.md']:
        paths.update((ROOT/'Hackaton/Semana 2/Codex').glob(pattern))
    paths.update([REPO/'registro/semana2_b20_contraccion2023_plan_v1.json',REPO/'src/semana2/diagnosticar_contraccion_b20_2023.py'])
    for path in read(RUN/'verification.json')['expected_failure_runs']:paths.update(x for x in (ROOT/path).rglob('*') if x.is_file())
    dump(RUN/'closure_manifest.json',{'utc':NOW,'notice':'Dated cut; subsequent legitimate shared appends do not rewrite this receipt.','files':[{'path':rel(x),'sha256':sha(x),'bytes':x.stat().st_size} for x in sorted(paths) if x.is_file()],'successful_fit_calls':0,'new_bootstrap':0,'reference':'W2-B00'})
    print(json.dumps({'closure_passed':receipt['passed'],'failed':receipt['failed'],'completed_units':len(newn['completed_units']),'concurrent_v1a_fixed20_max_error':max(errors.values()),'new_fits':0,'counter_values_cut':registration['counter_values_cut']},ensure_ascii=True))


if __name__=='__main__':main()
