"""Guarda un corte propio y conserva campos y aportes concurrentes."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
P=R/'registro/semana2_mision017_fase2_actual.json'
OUT=R/'privado/semana2/mision017_fase2/tanda1_20261025_v2'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))


def update(path,values,archive):
    before=path.read_bytes();text=before.decode('utf-8-sig');original=json.loads(text)
    for key,value in values.items():
        encoded=json.dumps(value,ensure_ascii=False,indent=2).replace('\n','\n  ')
        if key not in json.loads(text):text=text[:text.rfind('}')].rstrip()+',\n  '+json.dumps(key)+': '+encoded+'\n}\n'
        else:
            match=re.search(r'(?m)^  '+re.escape(json.dumps(key))+r':\s*',text);assert match
            _,end=json.JSONDecoder().raw_decode(text[match.end():])
            text=text[:match.end()]+encoded+text[match.end()+end:]
    assert {k:v for k,v in original.items() if k not in values}=={k:v for k,v in json.loads(text).items() if k not in values}
    after=text.encode('utf8');after=(b'\xef\xbb\xbf'+after) if before.startswith(b'\xef\xbb\xbf') else after
    save=archive/path.relative_to(ROOT);save.parent.mkdir(parents=True,exist_ok=True);save.write_bytes(before)
    tmp=path.with_name(path.name+'.phase2.tmp')
    with tmp.open('xb') as f:f.write(after);f.flush();os.fsync(f.fileno())
    assert path.read_bytes()==before,'Concurrencia detectada; conciliar antes de continuar.'
    os.replace(tmp,path)


def append(path,note,archive):
    before=path.read_bytes();save=archive/path.relative_to(ROOT);save.parent.mkdir(parents=True,exist_ok=True);save.write_bytes(before)
    tmp=path.with_name(path.name+'.phase2.tmp')
    with tmp.open('xb') as f:f.write(before+note.encode('utf8'));f.flush();os.fsync(f.fileno())
    assert path.read_bytes()==before;os.replace(tmp,path)


def main(mode):
    stamp=datetime.now(timezone.utc);tag=stamp.strftime('%Y%m%dT%H%M%SZ')
    archive=OUT/'state_cuts'/tag;archive.mkdir(parents=True,exist_ok=False)
    plan=R/'registro/semana2_mision017_fase2_tanda1_plan_v2.json'
    receipt={'utc':stamp.isoformat(),'phase':'tanda1','plan':rel(plan),'plan_sha256':sha(plan),
        'output':rel(OUT),'2024_open':True,'2024_is_adaptive_development':True,'goal_achieved':False}
    if mode=='running':
        started=read(OUT/'started.json');receipt.update(status='running',execution={'pid':started['pid'],'exec_session_id':2588,'started_utc':started['utc']},
            next_unit='Conciliar la misma sesión; completar diagnóstico preinscrito y replay sin ajuste. No lanzar otra tanda ni gastar envíos mientras esté pendiente.')
    else:
        report=OUT/'price_report.json';validation=OUT/'validation_v1/report.json'
        v=read(validation);receipt.update(status='completed_exploratory_batch',execution=None,price_report=rel(report),
            price_report_sha256=sha(report),validation=rel(validation),validation_sha256=sha(validation),scores=v['scores'],
            exploratory_pass=[n for n,z in v['comparisons'].items() if z['exploratory_pass']],
            next_unit='Revisar el fallo concreto de la comparación temporal antes de preinscribir la siguiente prueba; conservar F2 y los cupos. No confundir una mejora local con el objetivo público 0,17.')
    phase_values={'utc':stamp.isoformat(),'status':'active','current_batch':receipt,'next_unit':receipt['next_unit'],'2024_open':True,'2024_closed':False}
    if mode=='complete':
        phase_values.update(new_price_fits=12,new_C0_fits=15,new_emerging_C0_fits=0,new_closed_form_levels=6,new_submissions=0)
    update(P,phase_values,archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json'
    update(state,{'week_2_mission017_phase2_20261025':receipt},archive)
    if mode=='complete':
        counter=R/'registro/semana2_contadores_propios_actual.json';c=read(counter)
        assert 'phase2_2024_tanda1' not in c,'No duplicar contador de una tanda terminada.'
        update(counter,{'as_of_utc':stamp.isoformat(),'cumulative_price_base_fits':c['cumulative_price_base_fits']+12,
            'cumulative_closed_form_constants':c['cumulative_closed_form_constants']+6,
            'supplementary_reporting_peril_fits_since_counter_start':c['supplementary_reporting_peril_fits_since_counter_start']+15,
            'mixture_frequency_constants_since_counter_start_separate':c['mixture_frequency_constants_since_counter_start_separate']+15,
            'mixture_positive_severity_means_since_counter_start_separate':c['mixture_positive_severity_means_since_counter_start_separate']+45,
            'phase2_2024_tanda1':{'price_fits':12,'source_reporting_curves':15,'source_reporting_v1_partial':5,'source_reporting_v2_additional':10,
                'emerging_C0_fits':0,'closed_form_price_levels':6,'source_frequency_constants':15,
                'source_weighted_mark_means_3reserve_branches':45,'source_normalized_mixtures':3,
                'receipt':rel(validation),'receipt_sha256':sha(validation)}},archive)
        scores=v['scores'];cmp=v['comparisons']
        note='\n\n## Desarrollo con 2024: primera tanda temporal, 25 de octubre de 2026 (Bogotá)\n\n'
        note+=f'Codex, {stamp.isoformat()}. Entrenamiento emergente en 2023; evaluación de precios fijos en 2024. Fuente desarrollada 2021–2023, sin clima. Se conserva B00. D² local: '+', '.join(f'{n}={x:.6f}' for n,x in scores.items())+'.\n\n'
        for n,z in cmp.items():
            note+=f'{n}: diferencia frente a M0 {z["delta"]:+.6f}; IC95 por componentes [{z["bootstrap95"][0]:+.6f}, {z["bootstrap95"][1]:+.6f}]; '+f'criterios exploratorios completos: {z["exploratory_pass"]}. Fallos: '+', '.join(k for k,x in z['gates'].items() if not x)+'.\n\n'
        note+='Se completaron 12 ajustes de precio, 15 curvas de reporte de fuente y seis constantes de nivel. C0 emergente temporal se reutilizó sin reestimarlo. La versión inicial falló por códigos de construcción antes de ajustar precios; se conserva y sus cinco curvas de motor se reutilizaron. Replay numérico exacto y etiquetas retenidas alteradas sin efecto en las predicciones; ningún ajuste en ese replay.\n\n'
        note+='2024 es desarrollo adaptativo. El corte único de siniestros a diciembre 2024 y los maestros sin fecha impiden afirmar disponibilidad prospectiva completa; la cola y la suficiencia de reservas no están identificadas. Sin envíos nuevos ni promoción formal. La referencia pública del equipo sigue en 0,16033 y el objetivo 0,17 continúa activo. Evidencia: '+rel(validation)+'; plan: '+rel(plan)+'.\n'
        for n in ['MEMORIA_PROYECTO.md','DECISIONES.md']:append(ROOT/'Preparación'/n,note,archive)
        doc=R/'docs/semana2/MISION017_FASE2_TANDA1_2024.md';assert not doc.exists();doc.write_text(note,encoding='utf8')
        body=OUT/'forum_resultados.md';body.write_text(note,encoding='utf8')
        p=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
            '--id','COD-S2-20261025-MISION017-FASE2-TANDA1-RESULTADO','--asunto','Resultados temporales 2024 y límites de la primera tanda estándar',
            '--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
        receipt['forum']=json.loads(p.stdout)
    (archive/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(receipt,ensure_ascii=True))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['running','complete']);main(p.parse_args().mode)
