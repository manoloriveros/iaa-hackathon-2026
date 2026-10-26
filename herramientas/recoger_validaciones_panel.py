"""Recoge validaciones ya guardadas para el panel pedagógico. No ajusta ni puntúa."""
from __future__ import annotations
import hashlib
import json
import shutil
from datetime import datetime,timezone
from pathlib import Path
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=1,allow_nan=False)+'\n',encoding='utf-8')

def main():
    run=REPO/'privado/panel_validaciones'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');run.mkdir(parents=True,exist_ok=False)
    sources=[]
    def source(rel,label):
        p=REPO/rel;d=read(p);dest=run/'fuentes'/p.name;dest.parent.mkdir(exist_ok=True)
        if dest.exists():dest=dest.with_name(str(len(sources))+'_'+dest.name)
        shutil.copy2(p,dest);sources.append({'label':label,'path':p.relative_to(ROOT).as_posix(),'snapshot':dest.relative_to(ROOT).as_posix(),'sha256':sha(p)})
        return d
    base=source('docs/entrega/analisis/datos_panel.json','Datos de ambas semanas')
    c=source('docs/entrega/datos/cifras_entregables.json','Diagnósticos S30 guardados')
    nominal=source('registro/comparacion_privada_S30_S41_S42_S43_20261023.json','Público y privado de semana 1')
    portable=source('registro/reproduccion_m017_actual.json','Reproducción portable de F3c/F3d')
    submission=source('registro/semana2_control_entregas_codex_actual.json','Último recibo propio confirmado')
    gam=source('registro/semana2_GAM_validacion_privada_actual.json','Contraste exploratorio GAM, P17')
    gam_engine=source(str((ROOT/gam['engine_report']).relative_to(REPO)).replace('\\','/'),'Resultados completos GAM')
    p30=source('privado/semana2/mision017_fase2/P30_validacion_frecuencia_marca_20261026/P30_context_report.json','Criterios del GLM por peligro, P30')
    engine=source(str((ROOT/p30['raw_engine_report']).relative_to(REPO)).replace('\\','/'),'Resultados completos GLM por peligro')
    cohorts=source('privado/semana2/mision017_fase2/P30_validacion_frecuencia_marca_20261026/cohort_report.json','Clientes nuevos y corredor, P30')
    assert gam['formal_promotion'] is False and p30['formal_promotion'] is False
    assert 'F3c_F3d_exactos' in portable['estado']
    experiments=[]
    for id,label,raw,gates in [('P17','GAM con curvas',gam_engine,gam['primary_diagnostic_gates']),('P30','GLM por peligro',engine,p30['global_gates'])]:
        experiments.append({'id':id,'label':label,'baseline':'A1S / S2 / H1, receta experimental completa',
            'results':raw['results'],'gates':gates,'adopted':False,
            'scope':'Resultados exploratorios. Ambos años destino ya se usaron; la fuente incluye 2024. No es F3c reproducido.'})
    assert experiments[0]['results']['POOLED']['NOMINAL']['bootstrap95'][0]<0
    assert experiments[1]['results']['TRANSFER']['NOMINAL']['delta']<0
    d={'id':'PANEL-VALIDACIONES-20261026','author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'run':run.relative_to(ROOT).as_posix(),
       'base_data_sha256':sha(REPO/'docs/entrega/analisis/datos_panel.json'),'sources':sources,
       'week1':{'local':c['validacion']['d2_recalculado'],'baseline':c['validacion']['referencia_m00'],
           'means':c['validacion']['media_por_ramo'],'deciles':c['validacion']['deciles_v24'],
           'reserve_stress':c['validacion']['reservas'],'reporting_backtest':c['sensibilidad']['backtest_ibnr'],
           'influence':{'clients_flip_2024':c['sensibilidad']['clientes_que_invierten_la_ventaja_V24'],
               'clients_flip_2023':c['sensibilidad']['clientes_que_invierten_la_ventaja_V23'],'clients_2024':c['sensibilidad']['clientes_V24']},
           'reproduction':c['reproduccion_completa'],'scores':nominal['scores'],'score_source':nominal['fuente']},
       'week2':{'experiments':experiments,'cohorts':cohorts['comparisons'],
           'last_confirmed':submission['last_confirmed_own_submission'],
           'preflight':{k:{'checks':v['checks'],'rows':v['filas']} for k,v in portable['candidatos']['candidatos'].items()},
           'portable':{'utc':portable['utc'],'state':portable['estado'],'python':portable['env']['python'].split(' ')[0],
               'same_independent_reviewer':False,'full_source_training':False,'F4c_complete':False,
               'source_module_recovered':any(x['destino']=='f3_eval.py' for x in portable['insumos'])}},
       'training_in_this_task':False,'scores_computed_in_this_task':False,'source_review':'Inspección de recibos existentes; sin nueva evaluación predictiva.'}
    assert d['week2']['portable']['source_module_recovered']
    save(REPO/'docs/entrega/analisis/validaciones_panel.json',d);save(run/'validaciones_panel.json',d)
    for name in ['docs/entrega/panel_analisis.html','herramientas/compilar_paneles_analisis.py']:
        shutil.copy2(REPO/name,run/('antes_'+Path(name).name))
    save(REPO/'registro/panel_validaciones_actual.json',{'id':d['id'],'author':'Codex','run':d['run'],'state':'presentacion_en_preparacion','document_in_panel':False})
    print(json.dumps({'run':str(run),'sources':len(sources),'experiments':len(experiments)}))

if __name__=='__main__':main()
