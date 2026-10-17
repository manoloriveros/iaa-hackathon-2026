"""Nueva edición del explorador; conserva intactos el análisis, el primer informe y su fallo de QA."""
from datetime import datetime,timezone
from pathlib import Path
import json
import re
import shutil
import subprocess

import review_pairs as a


def main():
    pointer=json.loads((a.BASE/'current_run.json').read_text(encoding='utf-8'))
    run=a.ROOT/pointer['workspace_relative_run']
    m=json.loads((run/'manifest.json').read_text(encoding='utf-8'))
    assert all(a.c.digest(run/e['path'])==e['sha256'] for e in m['files'])
    ident=datetime.now(timezone.utc).strftime('explorer_fix_%Y%m%dT%H%M%SZ')
    edition=a.BASE/'editions'/ident;edition.mkdir(parents=True,exist_ok=False)
    for name in ['repair_report.py','render_pairs.py','verify_report.js']:shutil.copy2(a.BASE/name,edition/name)
    shutil.copy2(a.BASE/'current_run.json',edition/'index_before.json')
    failed=subprocess.run(['node',str(a.BASE/'verify_report.js'),str(run/'informe.html')],capture_output=True,text=True,encoding='utf-8')
    assert failed.returncode!=0 and 'value.slice is not a function' in failed.stderr
    (edition/'initial_report_failure.txt').write_text(failed.stderr,encoding='utf-8')
    html=(run/'informe.html').read_text(encoding='utf-8')
    old="if((field.endsWith('_date')||field.startsWith('period_'))&&value)"
    new="if(['loss_date','report_date','period_start','period_end'].includes(field)&&value)"
    assert html.count(old)==1;html=html.replace(old,new)
    prefix='../../runs/'+run.name+'/'
    html=re.sub(r'href="([^\"]+)"',lambda match:'href="'+(match.group(1) if match.group(1).startswith(('http:','https:','#','data:')) else prefix+match.group(1))+'"',html)
    html=html.replace('<h1>Revisión de los 604 pares potencialmente duplicados</h1>',
        '<h1>Revisión de los 604 pares potencialmente duplicados</h1><p>Edición verificada del explorador. El análisis y su primera versión se conservan sin cambios.</p>')
    (edition/'informe.html').write_text(html,encoding='utf-8')
    checked=subprocess.run(['node',str(a.BASE/'verify_report.js'),str(edition/'informe.html')],capture_output=True,text=True,encoding='utf-8',check=True)
    logic=json.loads(checked.stdout);assert logic['passed'] and logic['all_604_groups_exercised']
    a.c.dump(edition/'report_logic_verification.json',logic)
    assert all(a.c.digest(run/e['path'])==e['sha256'] for e in m['files'])
    assert a.c.digest(a.ROOT/'Hackaton/Semana 1/Limpieza/current_dataset.json')==a.c.digest(run/'evidence/active_index.json')
    pointer['initial_report_workspace_relative']=(run/'informe.html').relative_to(a.ROOT).as_posix()
    pointer['report_workspace_relative']=(edition/'informe.html').relative_to(a.ROOT).as_posix()
    pointer['report_repair_workspace_relative']=(edition/'verification.json').relative_to(a.ROOT).as_posix()
    a.c.dump(a.BASE/'current_run.json',pointer)
    a.c.dump(edition/'index_after.json',pointer)
    a.c.dump(edition/'verification.json',{'passed':True,'initial_failure':'Date suffix classification included monetary *_to_date fields; TypeError in explorer initialization.',
        'repair':'Only loss_date, report_date, period_start and period_end are formatted as dates.',
        'analysis_run_unchanged':True,'active_data_unchanged':True,'monetary_calculations_not_repeated':True,
        'all_604_groups_exercised':True,'report_logic_checks':logic['checks_count'],'browser_rendering_verified':False,
        'source_manifest_sha256':a.c.digest(run/'manifest.json'),'independent_validation':False})
    a.c.dump(edition/'manifest.json',{'files':[{'path':p.relative_to(edition).as_posix(),'sha256':a.c.digest(p),'bytes':p.stat().st_size}
        for p in sorted(edition.rglob('*')) if p.is_file()]})
    print(json.dumps({'edition':str(edition),'checks':logic['checks_count'],'all_groups':604,'data_unchanged':True}),flush=True)


if __name__=='__main__':main()
