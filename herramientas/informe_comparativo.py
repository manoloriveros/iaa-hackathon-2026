"""Cinco páginas comparativas; los datos de las 20 referencias quedan en privado.

Modos: datos (pandas/PyArrow), figuras (Matplotlib), pdf (ReportLab + PDFium).
No ajusta modelos ni calcula predicciones nuevas.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime,timezone
from decimal import Decimal,localcontext,ROUND_HALF_UP
from pathlib import Path
from xml.sax.saxutils import escape

REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
DOC=REPO/'docs/entrega/informe_final';CURRENT=REPO/'privado/entrega_final'
M={'developed':'Semana 1','emerging':'Semana 2'};L={'motor':'Autos','buildings':'Edificios','contents':'Contenidos'}
COL={'developed':'#21677d','emerging':'#bd5b32'}

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def f(v,n=0):return f'{float(v):,.{n}f}'.replace(',','@').replace('.',',').replace('@','.')

def aggregate(d,m,years,line=None):
    rows=[r for r in d['portfolio'] if r['market']==m and r['year'] in years and (line is None or r['line']==line)]
    return {k:sum(r[k] or 0 for r in rows) for k in ['rows','exposure','T0_cents','accepted','positive','positive_periods','reserve_cents','known_customers','exposure_changed']}

def prepare():
    sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
    import pandas as pd
    import pyarrow.parquet as pq
    run=REPO/'privado/informe_comparativo'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');run.mkdir(parents=True,exist_ok=False)
    sources=[]
    def source(p,role,expected=None):
        h=sha(p)
        if expected:assert h==expected,str(p)
        sources.append({'ruta':p.relative_to(ROOT).as_posix(),'sha256':h,'rol':role});return p
    d=read(source(REPO/'docs/entrega/analisis/datos_panel.json','EDA_comun'))
    source(REPO/'registro/panel_analisis_actual.json','indice_EDA')
    source(ROOT/'Hackaton/Semana 2/Claude/informe_final_20261026/informe_final_IAA2026_es.pdf','informe_previo_Claude')
    source(ROOT/'Hackaton/Semana 2/Claude/informe_final_20261026/fuente/paginas.py','redaccion_previa_Claude')
    for name in ['docs/RESULTADOS_PRIVADOS_SEMANA1.md','docs/SENSIBILIDAD_SEMANA2.md','docs/semana2/PRIVADA_P20_REQUISITOS_F3C.md','registro/semana2_control_entregas_codex_actual.json','registro/recibo_reproduccion_completa_20261020.json']:
        source(REPO/name,'evidencia_previa')
    base=ROOT/'Hackaton/Semana 2/Datos/emerging'
    ref_path=source(base/'reference_policies.parquet','20_referencias')
    expense_path=source(base/'expenses.parquet','gastos_oficiales')
    pred_path=source(REPO/'privado/semana2/claude_mision017_20261025/F3c_2025.csv','F3c_guardado','5ab5e4e34290cf6ed6a7a792f59e1e55a4f056400bbbdf8401933afd236b3276')
    ref=pq.read_table(ref_path).to_pandas();ex=pq.read_table(expense_path).to_pandas().set_index('item')
    pred=pd.read_csv(pred_path,dtype={'row_id':str,'prediction':str}).set_index('row_id')
    assert len(ref)==20 and ref.row_id.is_unique and pred.index.is_unique and len(pred)==209063
    assert ref.row_id.isin(pred.index).all()
    private=[];checks=[]
    with localcontext() as ctx:
        ctx.prec=45
        D=lambda v:Decimal(str(v))
        E=lambda key:D(ex.loc[key,'emerging'])
        for number,r in enumerate(ref.itertuples(index=False),1):
            risk=D(pred.loc[r.row_id,'prediction']);e=D(r.exposure)
            assert risk>=0 and e>0 and r.channel in ['broker','direct']
            commission=E('commission_'+r.channel);catrate=E('cat_reinsurance') if r.line in ['buildings','contents'] else D(0)
            den=1-E('variable_expense')-commission-E('premium_tax')-E('target_profit_margin')
            fixed=E('fixed_expense_per_policy')*e;cat=risk*catrate;price=(risk+cat+fixed)/den
            identity=risk+cat+fixed+price*(E('variable_expense')+commission+E('premium_tax')+E('target_profit_margin'))
            assert abs(identity-price)<D('1e-30') and den>0
            # Segundo método en float, separado de la identidad Decimal.
            float_price=(float(risk)*(1+float(catrate))+85*float(e))/(.69-float(commission))
            assert abs(float_price-float(price))<1e-8
            private.append({'ref':number,'row_id':r.row_id,'line':r.line,'channel':r.channel,'exposure':str(e),'R':str(risk),'cat':str(cat),'fixed':str(fixed),'P':str(price),'denominator':str(den)})
            checks.append({'ref':number,'identidad_decimal':True,'cotejo_float':True})
    # El panel reutiliza solo agregados; los registros de referencia no se embeben.
    manifest={'id':'INFORME-COMPARATIVO-20261026','autor_edicion':'Codex','autor_recetas_previas':'Claude y líneas originales según su registro',
        'utc':datetime.now(timezone.utc).isoformat(),'run':run.relative_to(ROOT).as_posix(),'sources':sources,
        'reference_count':len(private),'R_total':sum(float(x['R']) for x in private),'P_total':sum(float(x['P']) for x in private),
        'scope':'Datos, evidencia y precios guardados; sin entrenamiento, inferencia o selección.'}
    save(run/'referencias_comerciales.json',private);save(run/'controles_comerciales.json',checks);save(DOC/'datos_informe.json',manifest)
    shutil.copy2(REPO/'docs/entrega/informe_final/INFORME_ES.md',run/'plantilla_inicial.md')
    shutil.copy2(ROOT/'Hackaton/Semana 2/Claude/informe_final_20261026/informe_final_IAA2026_es.pdf',run/'informe_previo_Claude.pdf')
    CURRENT.mkdir(parents=True,exist_ok=True)
    if (CURRENT/'informe_dos_semanas.pdf').exists():shutil.copy2(CURRENT/'informe_dos_semanas.pdf',run/'informe_comun_anterior.pdf')
    save(REPO/'registro/informe_comparativo_actual.json',{'id':manifest['id'],'autor':'Codex','run':manifest['run'],'pdf':'privado/entrega_final/informe_dos_semanas.pdf','estado':'edicion_en_curso','references_in_git':False})
    print(json.dumps({'run':str(run),'refs':20,'R_total':manifest['R_total'],'P_total':manifest['P_total']}))

def figures():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    d=read(REPO/'docs/entrega/analisis/datos_panel.json');out=DOC/'figuras';out.mkdir(exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.spines.left':False,
        'axes.edgecolor':'#ced9de','axes.labelcolor':'#19394a','text.color':'#19394a','xtick.color':'#526b79','ytick.color':'#19394a','svg.fonttype':'none'})
    files=[]
    def finish(fig,name):
        fig.tight_layout(pad=1.1)
        for ext in ['png','svg']:
            p=out/(name+'.'+ext);fig.savefig(p,dpi=200,bbox_inches='tight',facecolor='white')
            if ext=='svg':p.write_text('\n'.join(s.rstrip() for s in p.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
            files.append({'path':p.relative_to(REPO).as_posix(),'sha256':sha(p)})
        plt.close(fig)
    fig,ax=plt.subplots(figsize=(8.3,1.95))
    for i,m in enumerate(M):
        vals=[]
        for y in [2024,2025]:
            a=aggregate(d,m,[y]);vals.append(100*(1-a['known_customers']/a['rows']))
        ax.plot(vals,[1-i,1-i],color=COL[m],linewidth=4,zorder=2)
        ax.scatter([vals[0]],[1-i],s=65,facecolor='white',edgecolor=COL[m],linewidth=2,zorder=4)
        ax.scatter([vals[1]],[1-i],s=65,color=COL[m],zorder=5)
        ax.text(101,1-i,f(vals[0],1)+' → '+f(vals[1],1)+' %',va='center',fontsize=10,color=COL[m])
    ax.set_yticks([1,0],['S1 · Desarrollado','S2 · Emergente']);ax.set_xlim(0,119);ax.set_xticks([0,25,50,75,100]);ax.set_xticklabels(['0','25','50','75','100 %']);ax.set_ylim(-.55,1.55);ax.grid(axis='x',color='#e5ecef',zorder=0)
    ax.set_title('Clientes sin registro anterior en su ramo · 2024 ○   2025 ●',loc='left',fontsize=11,pad=12)
    finish(fig,'clientes_comparados')
    fig,axes=plt.subplots(1,3,figsize=(8.5,2.9),sharey=True)
    metric=[('CU por año','T0_cents',lambda a:a['T0_cents']/100/a['exposure']),('Aceptados / 100 años','accepted',lambda a:100*a['accepted']/a['exposure']),('CU por siniestro positivo','positive',lambda a:a['T0_cents']/100/a['positive'])]
    yy=np.arange(3)
    for ax,(title,key,fn) in zip(axes,metric):
        all_values=[]
        for j,m in enumerate(M):
            vals=[fn(aggregate(d,m,[2023,2024],l)) for l in L];all_values+=vals
            ax.barh(yy+(j-.5)*.28,vals,height=.23,color=COL[m],label=M[m])
        ax.set_title(title,loc='left',fontsize=10,pad=12);ax.grid(axis='x',color='#e9eff1');ax.set_axisbelow(True);ax.set_xlim(0,max(all_values)*1.12);ax.locator_params(axis='x',nbins=3)
    axes[0].set_yticks(yy,list(L.values()));axes[0].invert_yaxis()
    fig.legend(handles=axes[0].get_legend_handles_labels()[0],labels=['S1 · Desarrollado','S2 · Emergente'],loc='lower center',ncol=2,frameon=False,bbox_to_anchor=(.54,-.065),fontsize=10)
    finish(fig,'experiencia_comparada')
    fig,ax=plt.subplots(figsize=(8.3,2.25));yy=np.arange(3)
    for j,m in enumerate(M):
        vals=[]
        for l in L:
            a=aggregate(d,m,[2024],l);vals.append(100*a['reserve_cents']/a['T0_cents'])
        ax.barh(yy+(j-.5)*.30,vals,height=.25,color=COL[m],label=M[m])
        for y,v in zip(yy+(j-.5)*.30,vals):ax.text(v+.4,y,f(v,1)+' %',va='center',fontsize=10,color=COL[m])
    ax.set_yticks(yy,list(L.values()));ax.invert_yaxis();ax.set_xlim(0,48);ax.set_xticks([0,10,20,30,40]);ax.set_xticklabels(['0','10','20','30','40 %']);ax.grid(axis='x',color='#e7eef1');ax.set_axisbelow(True)
    ax.legend(loc='lower right',frameon=False,ncol=2,fontsize=10);ax.set_title('Reserva de caso / T0 · 2024 · misma escala por ramo',loc='left',fontsize=11,pad=12)
    finish(fig,'reservas_comparadas')
    save(DOC/'figuras/manifest.json',{'data_sha256':sha(REPO/'docs/entrega/analisis/datos_panel.json'),'files':files})
    print('Tres figuras comparativas, PNG y SVG.')

def pdf():
    from reportlab.platypus import BaseDocTemplate,PageTemplate,Frame,Paragraph,Spacer,Table,TableStyle,Image,PageBreak,KeepTogether
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import pypdfium2 as pdfium
    from pypdf import PdfReader
    import pdfplumber
    from PIL import Image as PILImage
    d=read(REPO/'docs/entrega/analisis/datos_panel.json');meta=read(DOC/'datos_informe.json');run=ROOT/meta['run'];refs=read(run/'referencias_comerciales.json')
    for source in meta['sources']:assert sha(ROOT/source['ruta'])==source['sha256'],source['ruta']
    for name,file in [('Body','segoeui.ttf'),('Bold','segoeuib.ttf')]:pdfmetrics.registerFont(TTFont(name,'C:/Windows/Fonts/'+file))
    pdfmetrics.registerFontFamily('Body',normal='Body',bold='Bold',italic='Body',boldItalic='Bold')
    ink=colors.HexColor('#19394a');blue=colors.HexColor(COL['developed']);orange=colors.HexColor(COL['emerging']);W=A4[0]-34*mm
    S={
        'h1':ParagraphStyle('h1',fontName='Bold',fontSize=23,leading=27,textColor=ink,spaceAfter=11),
        'h2':ParagraphStyle('h2',fontName='Bold',fontSize=13,leading=17,textColor=blue,spaceBefore=10,spaceAfter=7,keepWithNext=True),
        'body':ParagraphStyle('body',fontName='Body',fontSize=9.7,leading=13.2,textColor=ink,spaceAfter=8),
        'small':ParagraphStyle('small',fontName='Body',fontSize=8,leading=10.5,textColor=colors.HexColor('#526b79'),spaceAfter=7),
        'cell':ParagraphStyle('cell',fontName='Body',fontSize=8.2,leading=10.2,textColor=ink),
        'head':ParagraphStyle('head',fontName='Bold',fontSize=8.1,leading=10,textColor=ink)}
    def P(text,style='body'):return Paragraph(escape(str(text)),S[style])
    def table(head,rows,widths=None,pricing=False):
        n=len(head);widths=widths or [W/n]*n
        values=[[P(v,'head') for v in head]]+[[P(v,'cell') for v in row] for row in rows]
        t=Table(values,colWidths=widths,hAlign='LEFT',repeatRows=1)
        styles=[('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#b9cbd3')),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#dce5e9')),
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#ecf2f5')),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]
        if pricing:styles += [('TOPPADDING',(0,1),(-1,-1),2.4),('BOTTOMPADDING',(0,1),(-1,-1),2.4)]
        else:
            for column,header in enumerate(head):
                if re.search(r'\bS1\b|Semana 1|Desarrollado',header):styles.append(('BACKGROUND',(column,0),(column,0),colors.HexColor('#dceaf0')))
                elif re.search(r'\bS2\b|Semana 2|Emergente',header):styles.append(('BACKGROUND',(column,0),(column,0),colors.HexColor('#f4e4dc')))
        t.setStyle(TableStyle(styles));return t
    tables={}
    train={m:aggregate(d,m,[2021,2022,2023,2024]) for m in M};test={m:aggregate(d,m,[2025]) for m in M}
    tables['TABLA_CARTERA']=table(['Dato','Semana 1 · Desarrollado','Semana 2 · Emergente'],[
        ['Historia de entrenamiento','2021-2024','2023-2024'],['Periodos históricos',f(train['developed']['rows']),f(train['emerging']['rows'])],
        ['Exposición histórica (años)',f(train['developed']['exposure'],1),f(train['emerging']['exposure'],1)],
        ['T0 observado (millones CU)',f(train['developed']['T0_cents']/1e8,2),f(train['emerging']['T0_cents']/1e8,2)],
        ['Periodos de test 2025',f(test['developed']['rows']),f(test['emerging']['rows'])]],[W*.36,W*.32,W*.32])
    rows=[]
    for l in L:
        a=aggregate(d,'developed',[2023,2024],l);b=aggregate(d,'emerging',[2023,2024],l)
        rows.append([L[l],f(a['T0_cents']/100/a['exposure'],2),f(b['T0_cents']/100/b['exposure'],2),f(100*a['accepted']/a['exposure'],2),f(100*b['accepted']/b['exposure'],2),f(a['T0_cents']/100/a['positive'],0),f(b['T0_cents']/100/b['positive'],0)])
    tables['TABLA_EXPERIENCIA']=table(['Ramo','CU/año S1','CU/año S2','Frec. S1','Frec. S2','Sev. S1','Sev. S2'],rows,[W*.16]+[W*.14]*6)
    q={x['market']:x for x in d['quality']}
    quality=[['Exposiciones históricas corregidas','14.229','609'],['Copias de siniestros excluidas','604','0'],['Ocurrencias anteriores a cobertura','413','36'],['Rechazados asignados, excluidos','1.701','120'],['Aceptados asignados a T0','160.432','9.102']]
    tables['TABLA_CALIDAD']=table(['Control','Semana 1','Semana 2'],quality,[W*.50,W*.25,W*.25])
    tables['TABLA_RESULTADOS']=table(['Medición','Semana 1 · S41','Semana 2 · F3c'],[
        ['Público archivado','0,13016','0,16914, corte 26 de octubre'],['Privado','0,13864, revelado','Aún no revelado'],['Selección definitiva','Registrada por participante','Pendiente en el corte']],[W*.36,W*.32,W*.32])
    tables['TABLA_CADENA']=table(['Paso emergente registrado','D² público','Diferencia'],[
        ['Mezcla inicial transferida','0,15390','-'],['Nivel global con credibilidad','0,15948','+0,00558'],['Historial de siniestros y bonificación','0,16033','+0,00085'],['Nivel/forma por celda','0,16519','+0,00486'],['Factores propios, F3c','0,16914','+0,00395']],[W*.62,W*.19,W*.19])
    tables['TABLA_GASTOS']=table(['Supuesto','Desarrollado','Emergente'],[
        ['Fijo anual / variable sobre prima','45 CU × e / 12 %','85 CU × e / 15 %'],['Corredor / directo','15 % / 0 %','20 % / 0 %'],['Impuesto / margen','12 % / 5 %','8 % / 8 %'],['Reaseguro sobre riesgo de hogar','6 %','12 %']],[W*.46,W*.27,W*.27],pricing=True)
    rounded=lambda v:Decimal(v).quantize(Decimal('.01'),rounding=ROUND_HALF_UP)
    money=lambda v:f(rounded(v),2)
    pricing=[[r['row_id'],L[r['line']],('Cor.' if r['channel']=='broker' else 'Dir.'),f(r['exposure'],4),money(r['R']),money(r['cat']),money(r['fixed']),money(r['P'])] for r in refs]
    pricing.append(['Total','20 referencias','','']+[f(sum(rounded(r[k]) for r in refs),2) for k in ['R','cat','fixed','P']])
    tables['TABLA_REFERENCIAS_PRIVADAS']=table(['Referencia','Ramo','Canal','e','Riesgo R','Cat.','Fijo','Comercial P'],pricing,[W*.17,W*.14,W*.08,W*.09,W*.13,W*.09,W*.09,W*.13],pricing=True)
    raw=(DOC/'INFORME_ES.md').read_text(encoding='utf-8');pages=raw.split('<!-- PAGE -->');assert len(pages)==5
    story=[];page_words=[]
    for pn,body in enumerate(pages,1):
        lines=body.strip().splitlines();i=0
        while i<len(lines):
            s=lines[i].strip()
            if not s:i+=1;continue
            if s.startswith('# '):story.append(P(s[2:],'h1'));i+=1;continue
            if s.startswith('## '):story.append(P(s[3:],'h2'));i+=1;continue
            marker=re.fullmatch(r'\{\{(TABLA_\w+)\}\}',s)
            if marker:story.extend([tables[marker[1]],Spacer(1,7)]);i+=1;continue
            image=re.fullmatch(r'!\[(.*?)\]\((.*?)\)',s)
            if image:
                p=DOC/image[2];w,h=PILImage.open(p).size
                target_width=W;target_height=target_width*h/w
                story.extend([Image(str(p),width=target_width,height=target_height),Spacer(1,5)]);i+=1;continue
            if s.startswith('|'):
                block=[]
                while i<len(lines) and lines[i].strip().startswith('|'):
                    row=[x.strip() for x in lines[i].strip().strip('|').split('|')]
                    if not all(re.fullmatch(r':?-+:?',x) for x in row):block.append(row)
                    i+=1
                widths=[W*.30,W*.35,W*.35] if len(block[0])==3 else None
                story.extend([table(block[0],block[1:],widths),Spacer(1,7)]);continue
            para=[s];i+=1
            while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','|','{{','![')):
                para.append(lines[i].strip());i+=1
            text=' '.join(para);style='small' if text.startswith(('IAA AI','Importes del','[S1]')) else 'body'
            story.append(P(text,style))
        if pn<5:story.append(PageBreak())
    class Doc(BaseDocTemplate):
        def afterFlowable(self,flowable):
            if isinstance(flowable,Paragraph) and flowable.style.name=='h1':page_words.append({'titulo':flowable.getPlainText(),'pagina':self.page})
    destination=CURRENT/'informe_dos_semanas.pdf'
    def footer(canvas,doc):
        canvas.setFillColor(colors.HexColor('#526b79'));canvas.setFont('Body',8)
        canvas.drawString(17*mm,12*mm,'IAA 2026 · Partes 1 y 2 · Revisión documental asistida por IA')
        canvas.drawRightString(A4[0]-17*mm,12*mm,f'{doc.page} / 5')
    doc=Doc(str(destination),pagesize=A4,leftMargin=17*mm,rightMargin=17*mm,topMargin=15*mm,bottomMargin=22*mm,title='IAA 2026 - Informe conjunto de cinco páginas',author='Manuel Rodríguez; edición documental de Codex')
    frame=Frame(17*mm,22*mm,W,A4[1]-37*mm,leftPadding=0,bottomPadding=0,rightPadding=0,topPadding=0)
    doc.addPageTemplates([PageTemplate(id='report',frames=[frame],onPage=footer)])
    doc.build(story)
    reader=PdfReader(destination);assert len(reader.pages)==5,f'El informe tiene {len(reader.pages)} páginas; se exigen cinco.'
    assert [x['pagina'] for x in page_words]==[1,2,3,4,5],page_words
    preview=run/'pdf';preview.mkdir(exist_ok=True);pdfdoc=pdfium.PdfDocument(str(destination));geometry=[]
    for i in range(5):
        page=pdfdoc[i];bitmap=page.render(scale=1.5);bitmap.to_pil().save(preview/f'pagina_{i+1}.png');bitmap.close();page.close()
    with pdfplumber.open(destination) as pdfdoc:
        for i,page in enumerate(pdfdoc.pages):
            words=page.extract_words();bad=[w for w in words if w['x0']<0 or w['x1']>page.width+.5 or w['top']<0 or w['bottom']>page.height]
            assert not bad
            text=page.extract_text() or '';assert '\ufffd' not in text
            geometry.append({'pagina':i+1,'palabras':len(words),'fuera_de_pagina':0})
    final_text='\n'.join(page.extract_text() or '' for page in reader.pages)
    for r in refs:assert final_text.count(r['row_id'])==1
    assert '0,13864' in final_text and '0,16914' in final_text and '76,04' in final_text
    shutil.copy2(destination,run/'informe_dos_semanas.pdf')
    save(run/'verificacion_pdf.json',{'pages':5,'geometry':geometry,'section_pages':page_words,'references_once':20,'pdf_sha256':sha(destination),'visual_review':'pendiente'})
    print(json.dumps({'pages':5,'pdf':str(destination),'run':str(run),'sha256':sha(destination)},ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('modo',choices=['datos','figuras','pdf']);mode=p.parse_args().modo
    {'datos':prepare,'figuras':figures,'pdf':pdf}[mode]()
