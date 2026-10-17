"""Amplía la lectura semántica de faltantes en una edición nueva, sin reescribir la corrida."""
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote
import json
import re
import shutil
import subprocess

import analyze_construction as a
import pandas as pd
import pyarrow.parquet as pq


def main():
    root = a.ROOT
    index = a.BASE / 'current_run.json'
    pointer = json.loads(index.read_text(encoding='utf-8'))
    run = root / pointer['workspace_relative_run']
    parent = json.loads((run / 'evidence/parent_catalog.json').read_text(encoding='utf-8'))
    source = root / parent['policies_buildings']['workspace_relative_path']
    assert a.c.digest(source) == parent['policies_buildings']['sha256']
    original_manifest_hash = a.c.digest(run / 'manifest.json')
    manifest = json.loads((run / 'manifest.json').read_text(encoding='utf-8'))
    assert all(a.c.digest(run / e['path']) == e['sha256'] for e in manifest['files'])
    pairs = pq.read_table(run / 'tables/boundary_2022_2023.parquet').to_pandas()
    pairs = pairs[pairs.previous_construction_type.eq('t')]
    f = pq.read_table(source,columns=['row_id','smoke_alarms','days_unoccupied']).to_pandas().set_index('row_id')
    records = []
    for field in ['smoke_alarms','days_unoccupied']:
        before = f.loc[pairs.previous_row_id,field].reset_index(drop=True)
        after = f.loc[pairs.row_id,field].reset_index(drop=True)
        both = before.notna() & after.notna()
        records.append({'field':field, 'pairs':len(pairs), 'both_observed':int(both.sum()),
            'both_observed_equal':int((both & before.eq(after)).sum()),
            'both_observed_different':int((both & before.ne(after)).sum()),
            'missing_to_observed':int((before.isna() & after.notna()).sum()),
            'observed_to_missing':int((before.notna() & after.isna()).sum()),
            'both_missing':int((before.isna() & after.isna()).sum())})
    details = pd.DataFrame(records)
    smoke,days = records
    assert smoke['pairs'] == 18218 and smoke['both_observed'] == 17346 and smoke['both_observed_different'] == 0
    assert smoke['missing_to_observed'] == 408 and smoke['observed_to_missing'] == 448 and smoke['both_missing'] == 16
    assert days['both_observed'] == 17330 and days['both_observed_different'] == 16273
    assert all(x['both_observed_equal'] + x['both_observed_different'] == x['both_observed'] for x in records)
    assert all(x['both_observed'] + x['missing_to_observed'] + x['observed_to_missing'] + x['both_missing'] == x['pairs'] for x in records)
    ident = datetime.now(timezone.utc).strftime('clarified_%Y%m%dT%H%M%SZ')
    edition = a.BASE / 'editions' / ident
    edition.mkdir(parents=True,exist_ok=False)
    shutil.copy2(Path(__file__), edition / Path(__file__).name)
    shutil.copy2(a.BASE / 'verify_report.js', edition / 'verify_report.js')
    shutil.copy2(index, edition / 'review_index_before.json')
    state_path = root / 'Preparación/ESTADO_PROYECTO.json'
    memory_path = root / 'Preparación/MEMORIA_PROYECTO.md'
    shutil.copy2(state_path, edition / 'state_before.json')
    details.to_csv(edition / 'paired_missingness_details.csv',index=False)
    a.c.dump(edition / 'paired_missingness_details.json',records)
    # Make links point to the immutable analysis artifacts from the new report location.
    content = (run / 'informe.html').read_text(encoding='utf-8')
    prefix = '../../runs/' + run.name + '/'
    content = re.sub(r'href="([^\"]+)"', lambda m:'href="' +
        (m.group(1) if m.group(1).startswith(('http:', 'https:', '#', 'data:')) else prefix + m.group(1)) + '"', content)
    old = '<p>Son idénticos el tomador, dirección, ocupación, cobertura de daño accidental, hipoteca, ambos deducibles, canal y forma de pago. Los días desocupados y algunas alarmas sí varían, como también ocurre en los controles. No se exige que todos los campos del riesgo sean estáticos para reconocer el cambio sistemático de etiqueta.</p>'
    assert content.count(old) == 1
    new = '''<p>Son idénticos el tomador, dirección, ocupación, cobertura de daño accidental, hipoteca, ambos deducibles, canal y forma de pago. La estabilidad de una característica física debe comprobarse separando valores observados y ausentes.</p>
<p>En smoke_alarms, los 17.346 pares informados en ambos años tienen exactamente el mismo valor: no hay un cambio observado de sí a no ni de no a sí. Las 856 diferencias del campo son 408 registros que pasan de ausente a informado y 448 que pasan de informado a ausente; otros 16 faltan en ambos años. El gráfico cuenta ambos ausentes como igualdad del registro, no como prueba de que hubiera alarma. Esa coincidencia no rellena ningún dato.</p>
<p>days_unoccupied tiene 17.330 pares informados en ambos años; 16.273 valores difieren. Es una medida de ocupación que puede variar entre periodos y no demuestra un cambio del material de construcción. El mapa T/W no exige falsa estabilidad de todos los campos.</p>
<details><summary>Desglose exacto de valores observados y ausentes</summary>''' + details.to_html(index=False,border=0) + '''<p><a href="paired_missingness_details.csv">Detalle CSV de esta ampliación</a></p></details>'''
    content = content.replace(old,new)
    content = content.replace('<h1>T y W: ¿dos construcciones o un cambio de código?</h1>',
        '<h1>T y W: ¿dos construcciones o un cambio de código?</h1><p>Edición con desglose de ausencias. La corrida y su informe inicial permanecen archivados sin cambios.</p>')
    (edition / 'informe.html').write_text(content,encoding='utf-8')
    report = subprocess.run(['node',str(a.BASE/'verify_report.js'),str(edition/'informe.html')],capture_output=True,text=True,encoding='utf-8',check=True)
    logic = json.loads(report.stdout)
    a.c.dump(edition / 'report_logic_verification.json',logic)
    class Links(HTMLParser):
        def __init__(self):super().__init__();self.paths=[]
        def handle_starttag(self,tag,attrs):
            self.paths.extend(value for key,value in attrs if key=='href' and value and not value.startswith(('http:','https:','#','data:')))
    links = Links(); links.feed(content)
    assert all((edition / unquote(p)).is_file() for p in links.paths)
    assert a.c.digest(run/'manifest.json') == original_manifest_hash and all(a.c.digest(run / e['path']) == e['sha256'] for e in manifest['files'])
    assert a.c.digest(root/'Hackaton/Semana 1/Limpieza/current_dataset.json') == a.c.digest(run/'evidence/active_dataset_before.json')
    pointer['initial_report_workspace_relative'] = (run/'informe.html').relative_to(root).as_posix()
    pointer['report_workspace_relative'] = (edition/'informe.html').relative_to(root).as_posix()
    pointer['missingness_detail_workspace_relative'] = (edition/'paired_missingness_details.csv').relative_to(root).as_posix()
    a.c.dump(index,pointer)
    state = json.loads(state_path.read_text(encoding='utf-8'))
    section = state['construction_review']
    section['initial_report'] = section['report']
    section['report'] = '../'+(edition/'informe.html').relative_to(root).as_posix()
    section['missingness_detail'] = '../'+(edition/'paired_missingness_details.csv').relative_to(root).as_posix()
    section['smoke_alarm_both_observed_pairs'] = 17346
    section['smoke_alarm_observed_value_changes'] = 0
    section['smoke_alarm_field_differences_due_only_to_missingness'] = 856
    a.c.dump(state_path,state)
    memory_path.write_text(memory_path.read_text(encoding='utf-8') + f'\nAmpliación de {section["decision_id"]}: el [informe con desglose de faltantes]({section["report"]}) distingue estabilidad física de ausencia de registro. smoke_alarms coincide en los 17.346 pares informados en ambos años; las 856 diferencias del campo son 408 ausente→informado y 448 informado→ausente; otros 16 faltan en ambos. days_unoccupied sí difiere en 16.273 de 17.330 pares informados. No se imputa nada ni cambia el mapa. La edición nueva conserva el informe y los 48 archivos de la corrida original por hash; el índice de revisión señala esta ampliación.\n',encoding='utf-8')
    a.c.dump(edition / 'verification.json', {'passed':True,'source_sha256':a.c.digest(source),
        'pairs_sha256':a.c.digest(run/'tables/boundary_2022_2023.parquet'),
        'source_analysis_manifest_sha256':original_manifest_hash, 'input_rows':18218,
        'counts_reconciled':True,'alarm_observed_value_changes':0,'missingness_not_imputed':True,
        'original_analysis_unchanged':True,'active_dataset_unchanged':True,'report_links_resolve':True,
        'report_logic_checks':logic['checks_count'],'browser_rendering_verified':False,
        'independent_validation':False,'further_model_or_data_transformation':False})
    a.c.dump(edition / 'review_index_after.json',pointer)
    shutil.copy2(state_path,edition / 'state_after.json')
    entries = [{'path':p.relative_to(edition).as_posix(),'sha256':a.c.digest(p),'bytes':p.stat().st_size}
               for p in sorted(edition.rglob('*')) if p.is_file()]
    a.c.dump(edition/'manifest.json', {'count':len(entries),'files':entries})
    print(json.dumps({'edition':str(edition),'alarm_observed_changes':0,'missingness_only_differences':856,
        'report_logic_passed':logic['passed'],'active_dataset_unchanged':True}),flush=True)


if __name__ == '__main__':main()
