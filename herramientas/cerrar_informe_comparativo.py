"""Sella la edición de cinco páginas y actualiza sus índices sin tocar modelos."""
from __future__ import annotations
import hashlib
import json
import shutil
from datetime import datetime,timezone
from decimal import Decimal,ROUND_HALF_UP
from pathlib import Path

REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
DOC=REPO/'docs/entrega/informe_final'

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def append_fields(path,fields):
    raw=path.read_bytes();s=raw.decode('utf-8-sig');old=json.loads(s);add={k:v for k,v in fields.items() if k not in old}
    if not add:return
    pos=s.rfind('}');new=s[:pos].rstrip()+',\n'+json.dumps(add,ensure_ascii=False,indent=2)[1:-1].strip('\n')+'\n'+s[pos:]
    json.loads(new);path.write_bytes(new.encode('utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'))

def main():
    from pypdf import PdfReader
    m=read(DOC/'datos_informe.json');run=ROOT/m['run'];ui=read(run/'verificacion_ui.json');pdf=read(run/'verificacion_pdf.json')
    assert ui['failed']==0 and ui['combinations']==96 and ui['passed']==508
    assert ui['html_sha256']==sha(REPO/'docs/entrega/panel_analisis.html')
    destination=REPO/'privado/entrega_final/informe_dos_semanas.pdf';assert pdf['pages']==5 and sha(destination)==pdf['pdf_sha256']
    for s in m['sources']:assert sha(ROOT/s['ruta'])==s['sha256'],s['ruta']
    # El índice previo es evidencia de la base EDA, no del diseño que ahora lo amplía.
    frozen=run/'fuentes';frozen.mkdir(exist_ok=True)
    for s in m['sources']:
        if s['ruta']=='Hackaton/Repositorio_IAA2026/registro/panel_analisis_actual.json':
            p=frozen/'indice_EDA_corte_previo.json';shutil.copy2(ROOT/s['ruta'],p);s['ruta']=p.relative_to(ROOT).as_posix();s['rol']='indice_EDA_corte_previo'
    refs=read(run/'referencias_comerciales.json');text='\n'.join(p.extract_text() or '' for p in PdfReader(destination).pages)
    assert not any(0xE000<=ord(c)<=0xF8FF for c in text),'Texto extraído con caracteres privados'
    assert all(text.count(r['row_id'])==1 for r in refs)
    html=(REPO/'docs/entrega/panel_analisis.html').read_text(encoding='utf-8')
    source=(DOC/'INFORME_ES.md').read_text(encoding='utf-8')
    assert all(r['row_id'] not in html and r['row_id'] not in source for r in refs)
    assert '{{TABLA_REFERENCIAS_PRIVADAS}}' in source
    rounded=lambda v:Decimal(v).quantize(Decimal('.01'),rounding=ROUND_HALF_UP)
    totals={k:str(sum(rounded(r[k]) for r in refs)) for k in ['R','cat','fixed','P']}
    m['displayed_totals_CU']=totals;save(DOC/'datos_informe.json',m)
    pdf.update({'visual_review':'Cinco páginas inspeccionadas por Codex, sin recortes o solapamientos visibles','professional_independent_validation':False,'text_without_private_use_glyphs':True})
    save(run/'verificacion_pdf.json',pdf)
    snapshots=run/'codigo_final';snapshots.mkdir(exist_ok=True)
    paths=['herramientas/informe_comparativo.py','herramientas/verificar_comparacion.cjs','herramientas/verificar_panel_analisis.cjs',
        'herramientas/compilar_paneles_analisis.py','herramientas/cerrar_informe_comparativo.py','docs/entrega/web/comparacion_plantilla.html','docs/entrega/informe_final/INFORME_ES.md']
    for name in paths:shutil.copy2(REPO/name,snapshots/Path(name).name)
    for entry in read(DOC/'figuras/manifest.json')['files']:assert sha(REPO/entry['path'])==entry['sha256']
    utc=datetime.now(timezone.utc).isoformat()
    receipt={'id':'INFORME-COMPARATIVO-20261026','autor':'Codex','utc':utc,'pdf_pages':5,'pdf_sha256':pdf['pdf_sha256'],
        'html_sha256':ui['html_sha256'],'ui_checks':ui['passed'],'ui_combinations':96,'ui_errors':ui['errors'],'http_requests':ui['network'],
        'reference_prices':20,'pricing_identity':'Decimal y cotejo alternativo float en cada referencia','totals_displayed_CU':totals,
        'visual_review':'realizada_por_Codex','independent_professional_review':False,'participant_report_approval':'pendiente',
        'training':False,'new_predictions':False,'submission':False,'publication':False,'final_selection_modified':False,
        'code':[{'path':p,'sha256':sha(REPO/p)} for p in paths],
        'outputs':[{'path':p,'sha256':sha(REPO/p)} for p in ['privado/entrega_final/informe_dos_semanas.pdf','docs/entrega/panel_analisis.html','docs/entrega/informe_final/datos_informe.json','docs/entrega/informe_final/INFORME_ES.md']]}
    save(run/'recibo_final.json',receipt)
    public={k:v for k,v in receipt.items() if k not in ['code','outputs']};public['receipt_workspace_relative']=(run/'recibo_final.json').relative_to(ROOT).as_posix();save(DOC/'VERIFICACION.json',public)
    index=read(REPO/'registro/informe_comparativo_actual.json');index.update({'utc':utc,'estado':'informe_cinco_paginas_y_comparacion_verificados_localmente',
        'path_base':'repository_root','run_base':'workspace_root','source':'docs/entrega/informe_final/INFORME_ES.md','panel':'docs/entrega/panel_analisis.html',
        'validation':'docs/entrega/informe_final/VERIFICACION.json','pdf_sha256':pdf['pdf_sha256'],'html_sha256':ui['html_sha256'],
        'pdf_pages':5,'ui_checks':508,'ui_combinations':96,'pricing_references':20,'human_approval':'pendiente','selection_part2':'abierta; F3c solo referencia medida'})
    save(REPO/'registro/informe_comparativo_actual.json',index)
    old=read(REPO/'registro/panel_analisis_actual.json');old['presentacion_actual']={'path_base':'repository_root','index':'registro/informe_comparativo_actual.json','html_sha256':ui['html_sha256'],'ui_checks':508,'ui_combinations':96,'utc':utc,'baseline_receipt_preserved':True};save(REPO/'registro/panel_analisis_actual.json',old)
    append_fields(ROOT/'RUTAS_PROYECTO.json',{'joint_final_report':'Hackaton/Repositorio_IAA2026/privado/entrega_final/informe_dos_semanas.pdf',
        'joint_final_report_source':'Hackaton/Repositorio_IAA2026/docs/entrega/informe_final/INFORME_ES.md','joint_final_report_index':'Hackaton/Repositorio_IAA2026/registro/informe_comparativo_actual.json'})
    append_fields(ROOT/'Preparación/ESTADO_PROYECTO.json',{'informe_comparativo_dos_semanas_20261026':{'utc':utc,'author':'Codex','path_base':'workspace_root',
        'status':'five_total_pages_and_comparison_dashboard_verified','index':'Hackaton/Repositorio_IAA2026/registro/informe_comparativo_actual.json',
        'pdf_pages':5,'ui_checks':508,'ui_combinations':96,'commercial_references':20,'training':False,'new_predictions':False,'selection_part2':'open_not_changed','human_approval':'pending'}})
    note='''

## Informe conjunto de cinco páginas y presentación comparativa, 26 de octubre de 2026

Codex. El participante pidió integrar hallazgos y figuras en el informe final de ambas semanas y facilitar la comparación. Se creó la edición común de cinco páginas totales en `Hackaton/Repositorio_IAA2026/privado/entrega_final/informe_dos_semanas.pdf`, desde el informe conjunto anterior de Claude y el EDA común verificado. El original de Claude y los informes previos de semana 1 se conservan. La fuente editable y las tres figuras están en `docs/entrega/informe_final/`; el índice es `registro/informe_comparativo_actual.json`.

Las páginas comparan datos y cambio de cartera; experiencia 2023-2024; modelos/resultados; validación/IA; y gastos/primas comerciales. Azul constante para semana 1, naranja para semana 2, columnas y barras emparejadas con escalas comunes. Se distinguen volúmenes de historias diferentes, incurrido observado/último, público/privado y revisión de IA/profesional. S41 sigue seleccionada en parte 1. F3c es la referencia pública medida al corte, no una nueva marca final de parte 2.

Las veinte referencias se enlazaron al F3c guardado cuyo SHA es 5ab5e4e34290cf6ed6a7a792f59e1e55a4f056400bbbdf8401933afd236b3276. Sus primas comerciales se calcularon con gastos oficiales, identidad Decimal y cotejo float; sin inferencia o modelos nuevos. El total de las filas redondeadas es 20.304,23 CU (riesgo 9.005,76 CU). Los importes por referencia quedan solo en privado, fuera de Git y del dashboard. El total se distingue del redondeo de la suma sin redondear.

El dashboard `docs/entrega/panel_analisis.html` ahora compara ambos mercados simultáneamente, con años/ramo comunes, seis indicadores y diferencias relativas. Pasa 508 comprobaciones en 96 selecciones, exportación con nulos de test, teclado, impresión, enlaces y cuatro anchos; cero errores JS o solicitudes HTTP(S). El PDF tiene cinco páginas y cada referencia aparece una sola vez; las cinco PNG se revisaron visualmente. Se conservan un intento de seis páginas y el error de ruta del comprobador que escapaba #limites. Los recibos del EDA previo se preservan y la presentación actual tiene su propio índice.

No se entrenó, predijo, envió, publicó o cambió selección. No se repitió el cotejo de 2,5 millones de etiquetas por un cambio de presentación: se reutiliza la base verificada y se comprueban figuras, fórmulas, referencias y salidas nuevas. Aprobación humana del informe, selección definitiva de semana 2 y reproducción profesional independiente permanecen pendientes.
'''
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:
        p=ROOT/'Preparación'/name
        if '## Informe conjunto de cinco páginas y presentación comparativa, 26 de octubre de 2026' not in p.read_text(encoding='utf-8-sig'):
            with p.open('a',encoding='utf-8',newline='') as stream:stream.write(note)
    print(json.dumps({'pages':5,'ui_checks':508,'pricing_references':20,'pdf':str(destination),'receipt':str(run/'recibo_final.json')},ensure_ascii=False))

if __name__=='__main__':main()
