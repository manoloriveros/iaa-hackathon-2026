"""Cierra recibos del panel; solo actualiza su índice y memoria, sin entrenar."""
from __future__ import annotations
import hashlib
import json
import shutil
from datetime import datetime,timezone
from pathlib import Path
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]


def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def add_root_fields(path,fields):
    """Añade objetos sin reescribir el prefijo histórico del JSON."""
    raw=path.read_bytes();text=raw.decode('utf-8-sig');old=json.loads(text)
    absent={k:v for k,v in fields.items() if k not in old}
    if not absent:return
    tail=text.rfind('}')
    addition=json.dumps(absent,ensure_ascii=False,indent=2)[1:-1].strip('\n')
    new=text[:tail].rstrip()+',\n'+addition+'\n'+text[tail:]
    json.loads(new)
    path.write_bytes(new.encode('utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'))


def main():
    d=read(REPO/'docs/entrega/analisis/datos_panel.json');run=ROOT/d['private_run']
    core=read(run/'validacion_separada.json');climate=read(run/'validacion_clima.json');ui=read(run/'validacion_ui.json')
    current=sha(REPO/'docs/entrega/analisis/datos_panel.json')
    assert core['data_sha256']==climate['base_data_sha256']==sha(run/'datos_antes_clima.json')
    assert climate['final_data_sha256']==ui['data_sha256']==current
    assert all(x['failed']==0 for x in [core,climate,ui])
    for x in d['sources']:assert sha(ROOT/x['ruta'])==x['sha256'],x['ruta']
    figures=read(REPO/'docs/entrega/analisis/figuras/manifest.json');assert figures['data_sha256']==current
    for x in figures['files']:assert sha(REPO/x['ruta'])==x['sha256']
    pdf=read(run/'pdf/recibo.json');assert sha(REPO/'docs/entrega/analisis/anexo_datos_dos_semanas.pdf')==pdf['sha256']
    pdf.update({'revision_visual':'realizada_por_Codex_sin_recortes_o_solapamientos','revisor':'Codex','professional_independent_validation':False})
    save(run/'pdf/recibo.json',pdf)
    assert 'entrega/panel_analisis.html' in (REPO/'docs/panel_revision.html').read_text(encoding='utf-8')
    utc=datetime.now(timezone.utc).isoformat()
    artifacts=['docs/entrega/panel_analisis.html','docs/entrega/panel_modelo.html','docs/entrega/web/analisis_plantilla.html',
        'docs/entrega/web/panel_plantilla.html','docs/entrega/analisis/datos_panel.json','docs/entrega/analisis/ANALISIS_DOS_SEMANAS.md',
        'docs/entrega/analisis/TEXTO_PARA_INFORME.md','docs/entrega/analisis/VALIDACION_PANEL.md','docs/entrega/analisis/anexo_datos_dos_semanas.pdf']
    scripts=['construir_panel_analisis.py','verificar_panel_analisis.py','verificar_panel_analisis.cjs','complementar_clima_panel.py',
        'compilar_paneles_analisis.py','preparar_anexo_analisis.py','cerrar_panel_analisis.py']
    code=run/'codigo_final';code.mkdir(exist_ok=True)
    for name in scripts:shutil.copy2(REPO/'herramientas'/name,code/name)
    shutil.copy2(REPO/'docs/entrega/web/analisis_plantilla.html',code/'analisis_plantilla.html')
    attempts={'ui':['Playwright sin Chromium empaquetado','Edge se cerró dentro del aislamiento','Descarga cancelada dentro del aislamiento; Chrome fuera del aislamiento pasó exportación real'],
        'data':'Primera revisión interrumpida por ordenación repetida; código conservado. Ordenación global terminada sin fallos.',
        'pdf':'Leyenda del volumen movida al espacio superior; cuatro páginas finales inspeccionadas.'}
    save(run/'intentos_y_correcciones.json',attempts)
    receipt={'id':'PANEL-DATOS-S1-S2-20261026','autor':'Codex','utc':utc,'data_sha256':current,
        'results':{'producer':d['validation']['controls'],'separate':core['passed'],'climate':climate['passed'],'ui':ui['passed'],'filter_combinations':ui['combinations'],'pdf_pages':pdf['paginas']},
        'artifacts':[{ 'path':x,'sha256':sha(REPO/x)} for x in artifacts],
        'code':[{ 'path':'herramientas/'+x,'sha256':sha(REPO/'herramientas'/x)} for x in scripts],
        'training':False,'inference':False,'submissions':False,'publication':False,'professional_independent_validation':False,
        'human_report_approval':'pendiente; no se firma por inferencia'}
    save(run/'validacion_final.json',receipt)
    index=read(REPO/'registro/panel_analisis_actual.json')
    index.update({'estado':'verificado_localmente_con_revisión_visual_propia','utc':utc,'data_sha256':current,
        'validation':receipt['results'],'receipt':(run/'validacion_final.json').relative_to(ROOT).as_posix(),
        'receipt_sha256':sha(run/'validacion_final.json'),'pdf':'docs/entrega/analisis/anexo_datos_dos_semanas.pdf',
        'report_text':'docs/entrega/analisis/TEXTO_PARA_INFORME.md','professional_independent_validation':False})
    save(REPO/'registro/panel_analisis_actual.json',index)
    add_root_fields(ROOT/'RUTAS_PROYECTO.json',{
        'joint_data_dashboard':'Hackaton/Repositorio_IAA2026/docs/entrega/panel_analisis.html',
        'joint_data_analysis_report':'Hackaton/Repositorio_IAA2026/docs/entrega/analisis/ANALISIS_DOS_SEMANAS.md',
        'joint_data_analysis_pdf':'Hackaton/Repositorio_IAA2026/docs/entrega/analisis/anexo_datos_dos_semanas.pdf',
        'joint_data_analysis_index':'Hackaton/Repositorio_IAA2026/registro/panel_analisis_actual.json'})
    entry={'utc':utc,'author':'Codex','path_base':'workspace_root','status':'verified_local_descriptive_dashboard_no_training',
        'index':'Hackaton/Repositorio_IAA2026/registro/panel_analisis_actual.json','results':receipt['results'],
        'scope':'Datos de ambas semanas; T0 observado reconstruido por fila, exposición, siniestros, nulos, clima y composición 2025.',
        'limit':'Revisión propia, 2024 adaptativo, sin último observado, sin adopción de modelos o publicación.'}
    add_root_fields(ROOT/'Preparación/ESTADO_PROYECTO.json',{'panel_analisis_dos_semanas_20261026':entry})
    note='''

## Panel de análisis de ambas semanas, 26 de octubre de 2026

Codex. Por solicitud del participante se complementa el panel anterior con `Hackaton/Repositorio_IAA2026/docs/entrega/panel_analisis.html`, enlazado desde los paneles de revisión y modelo. Incluye filtros por mercado, ramo y año, exposición conciliada, T0, frecuencia/severidad, reservas, peligros, retrasos truncados, nulos ponderados y diferencias de esquema. Clima enlazado por dirección/año y test 2025 sin etiquetas. No se entrena, carga modelos, selecciona envíos ni publica.

T0 reconstruido coincide por fila con ambas bases: 741.156.868,43 CU desarrolladas y 27.997.991,57 CU emergentes. Se conservan 604 copias excluidas y 413 anteriores a cobertura en desarrollado; 36 anteriores en emergente. Son exclusiones descriptivas, sin inventar una causa operativa. Exposición inclusiva días/365, con 14.229 y 609 filas históricas corregidas; test sin cambios. El 76,04 % de los periodos emergentes 2025 no tiene cliente previo en su ramo, frente al 15,19 % desarrollado; no equivale al campo new_business.

Evidencia final: 136 controles del productor, 1.927 de la comprobación separada (Decimal, sumas escalares, intervalos por búsqueda binaria y nulos), 196 de clima y 231 de UI, con 96 combinaciones de filtros, cero errores JS y cero solicitudes de red. Son bloques parcialmente solapados, no validaciones independientes sumables. La descarga cancelada dentro del aislamiento pasó con Chrome fuera de ese aislamiento; se conserva el intento de ordenación lenta interrumpido. PDF de cuatro páginas y tres figuras PNG/SVG revisados visualmente. Índice: `Hackaton/Repositorio_IAA2026/registro/panel_analisis_actual.json`.

El anexo editable/PDF y `TEXTO_PARA_INFORME.md` quedan en `docs/entrega/analisis/`, listos para incorporar al informe conjunto. El informe competitivo previo conserva su alcance de semana 1; no se declara actualizado todo el cuerpo final ni seleccionada la semana 2. T0 no es último, 2024 sigue adaptativo y clima 2025 no acredita disponibilidad al cotizar. La comisión emergente de comparison_site sigue vacía. Revisión propia de Codex, sin aprobación humana general o validación profesional independiente atribuida. Originales y corridas previas conservados.
'''
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:
        p=ROOT/'Preparación'/name
        if '## Panel de análisis de ambas semanas, 26 de octubre de 2026' not in p.read_text(encoding='utf-8-sig'):
            with p.open('a',encoding='utf-8',newline='') as stream:stream.write(note)
    print(json.dumps({'index':str(REPO/'registro/panel_analisis_actual.json'),'results':receipt['results'],'sha256':current},ensure_ascii=False))


if __name__=='__main__':main()
