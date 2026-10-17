"""Contraste documental de fuentes, cifras, enlaces y lógica local; no reejecuta reglas."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
from decimal import Decimal
import json
import re
import subprocess
import sys
import collect_documentation as a
import clean_data as c
import pandas as pd
import pyarrow.parquet as pq


class Document(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True);self.refs=[];self.ids=[];self.fields=[];self.tables=[];self.rows=0;self.scripts=[];self.inscript=False;self.script=''
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if attrs.get('id'):self.ids.append(attrs['id'])
        for key in ['href','src']:
            if attrs.get(key):self.refs.append(attrs[key])
        if tag=='article' and attrs.get('class')=='field':self.fields.append({'id':attrs['id'],'search':attrs['data-search']})
        if tag=='table':self.rows=0
        if tag=='tr':self.rows+=1
        if tag=='script':self.inscript=True;self.script=''
    def handle_endtag(self,tag):
        if tag=='table':self.tables.append(self.rows-1)
        if tag=='script':self.inscript=False;self.scripts.append(self.script)
    def handle_data(self,data):
        if self.inscript:self.script+=data


def main(out):
    assert not (out/'manifest.json').exists()
    checks=[]
    def check(label,ok):
        checks.append({'check':label,'passed':bool(ok)})
        if not ok:
            c.dump(out/'documentation_verification_failure.json',{'status':'failed_not_closed','checks':checks});raise AssertionError(label)
    f=a.readj(out/'facts.json');sources=a.readj(out/'source_register.json');dictionary=a.readj(out/'dictionary_107.json')
    check('All protected originals, active files, dataset indexes, protocol and guards unchanged',all(c.digest(c.ROOT/path)==sha for path,sha in a.readj(out/'protected_data_hashes.json').items()))
    for key,row in sources.items():
        check(row['source_id']+': source file matches recorded hash at documentation check',c.digest(c.ROOT/row['workspace_relative_path'])==row['sha256'])
        if row.get('snapshot'):check(row['source_id']+': frozen snapshot matches consulted content',c.digest(out/row['snapshot'])==row['sha256'])
    d28=a.readj(c.ROOT/sources['report_workspace_layout_review']['workspace_relative_path']);d28files={row['name']:row for row in d28['files']}
    for row in f['raw_tables']:
        known=d28files[row['table']+'.parquet'];q=pq.ParquetFile(c.RAW/(row['table']+'.parquet'))
        check(row['table']+': original SHA and schema/row metadata match D28 and dossier',known['sha256']==row['sha256'] and known['rows_metadata']==q.metadata.num_rows==row['rows'] and len(q.schema_arrow)==row['columns'] and q.schema_arrow.names==row['column_names'])
    check('105 original names,242 occurrences and107 derived names,249 occurrences',f['original_unique_columns']==105 and f['original_column_occurrences']==242 and f['derived_unique_columns']==107 and f['derived_column_occurrences']==249)
    p=pd.read_parquet(c.ROOT/sources['current_pending']['workspace_relative_path']);cum=pd.read_parquet(c.ROOT/sources['retrospective_ledger']['workspace_relative_path']);cap01=pd.read_parquet(c.ROOT/sources['CAP01_ledger']['workspace_relative_path'])
    pd.testing.assert_frame_equal(p,pd.read_parquet(out/'tables/pending_419_snapshot.parquet'),check_exact=True)
    check('419 pending snapshot equals active inventory in every field/order',len(p)==p.row_id.nunique()==419)
    pd.testing.assert_frame_equal(cum,pd.read_parquet(out/'tables/retrospective_1035_snapshot.parquet'),check_exact=True)
    check('1035 cumulative rows and3108 distinct corrected capitals exactly reconcile',len(cum)==cum.row_id.nunique()==1035 and len(cap01)==2073 and len(set(cum.row_id)|set(cap01.row_id))==3108 and not set(p.row_id)&(set(cum.row_id)|set(cap01.row_id)))
    check('177 pending test rows in CAP06R,190 only in base',int(p.source_table.str.startswith('test_').sum())==177 and f['base_pending_extremes']==1454 and f['retrospective_pending_extremes']==419)
    check('Current group counts sum419 with154/138/108/16/2/1',p.review_group.value_counts().to_dict()=={'F_incomplete_context':154,'G_other_conflicts':138,'C_no_original_normal_reference':108,'E_TW_dependency':16,'D_CAP01_dependency_only':2,'A_retrospective_D34':1})
    expected_rules={'CAP02R':867,'CAP03R':11,'CAP04R':109,'CAP05R':46,'CAP06R':2}
    check('Rule counts and136 future test anchors,13 corrected retrospective test rows',cum.rule.value_counts().to_dict()==expected_rules and int(cum.audit_ref_test2025.sum())==136 and int(cum.source_table.str.startswith('test_').sum())==13)
    running=2073
    for row in f['capital_stages']:
        if row['rule']=='CAP01':count=len(cap01);anchors=0
        else:
            part=cum.loc[cum.rule.eq(row['rule'])];count=len(part);anchors=int(part.audit_ref_test2025.sum());running+=count
        check(row['rule']+': stage arithmetic, pending and anchor counts',row['rows']==count and row['new_test2025_anchors']==anchors and row['cumulative_corrected']==running and running+row['remaining']==3527)
    clean=a.readj(c.ROOT/sources['data_cleaning_summary']['workspace_relative_path']);refine=a.readj(c.ROOT/sources['data_refinement_summary']['workspace_relative_path'])
    check('ID01 andEXP01 counts reconcile historical authoritative summaries',sum(x['id_changes'] for x in clean)==123664 and sum(x['exposure_changes'] for x in clean)==14229 and f['cleaning_summary']==clean)
    check('CAT01 andAGE01 counts reconcile historical authoritative summaries',sum(x['category_changes'] for x in refine)==700210 and sum(x['age_changes'] for x in refine)==2936 and f['refinement_summary']==refine)
    age=f['AGE01_D59_explanation'];check('AGE01 explains2934 and leaves2, without claiming2936 source errors',age=={'discrepancies':2936,'explained_by_age_at_quote_date':2432,'explained_by_birthday_on_period_start_exclusive':457,'plus_one_explained_by_age_at_period_end':45,'unexplained':2})
    check('D59 summary41 checks scoped toCAP05R and no independent human validation',f['D59_summary']['checks_passed']==41 and f['D59_summary']['independent_validation'] is False and f['D59_actual_retrospective_run'].endswith('capdistant_20261017T004534Z_6e8f8e18'))
    check('CAP06R proof279 own controls read from immutable current run',a.readj(c.ROOT/sources['CAP06R_verification']['workspace_relative_path'])['passed']==279)
    dups=f['audit_counts']['duplicate_application'];pre=f['audit_counts']['prehistory_audit_application'];ren=f['audit_counts']['renewal_audit_application']
    check('DUP01 metadata163150→162546,604exclusions and exact financial split',dups['source_rows']-dups['excluded_records']==dups['derived_rows']==162546 and dups['excluded_records']==604 and Decimal(dups['net_accepted_reduction_assigned_CU'])+Decimal(dups['net_accepted_reduction_prehistory_CU'])==Decimal(dups['net_accepted_reduction_CU'])==Decimal('3174167.49'))
    check('PRE00 andREN00 counts and financial scope exact',pre['marked_claims']==413 and pre['accepted_marked_claims']==409 and Decimal(pre['marked_net_accepted_CU'])==Decimal('1721459.84') and ren['marked_period_rows']==12041 and ren['frozen_policies']==2742)
    probe=a.readj(out/'guard_probe.json');check('Documented contact guard gap still actual',a.predictor_guard.exclusion_reason('customer_service_contacts') is None and probe['customer_service_contacts'] is None and 'customer_service_contacts' in probe['selection_example'] and all(probe[x] for x in ['renewal_decision','audit_ren00','audit_pre00']))
    check('Exact107 dictionary names cover current catalog without omissions',len(dictionary)==len({row['column'] for row in dictionary})==107 and set(row['column'] for row in dictionary)==set().union(*(set(row['column_names']) for row in f['current_tables'] if row['layer']=='retrospective')))
    notes=pd.read_csv(c.ROOT/sources['column_notes_D30']['workspace_relative_path'],sep='\t').set_index('column')
    for row in dictionary:
        if row['column'] in notes.index:
            check(row['column']+': original D30 meaning, insurance explanation and availability preserved',all(row[col]==notes.loc[row['column'],col] for col in ['meaning','insurance_and_tariff','availability']))
        check(row['column']+': no accidental F0 approval',row['operational_F0_contract_complete'] is False)
    backlog=a.readj(out/'validation_register_58.json');old=a.readj(c.ROOT/sources['backlog_D56']['workspace_relative_path'])
    check('Exactly58 original controlIDs with priorities and closure criteria preserved',len(backlog)==58 and {row['id'] for row in backlog}=={row['id'] for row in old} and all(row['priority']==src['priority'] and row['closure_criterion']==src['closure_criterion'] for row,src in zip(backlog,old)) and not any(row['fresh_rule_reexecution'] for row in backlog))
    pages={}
    future={'documentation_verification.json','manifest.json'}
    for filename in ['informe.html','diccionario.html','validaciones.html','decisiones.html','fuentes.html']:
        parser=Document();parser.feed((out/filename).read_text('utf-8'));pages[filename]=parser
        check(filename+': no duplicate element IDs',len(parser.ids)==len(set(parser.ids)))
        for ref in parser.refs:
            parts=urlsplit(ref)
            check(filename+': local reference '+ref,not parts.scheme and not parts.netloc)
            target=(out/unquote(parts.path)).resolve() if parts.path else out/filename
            check(filename+': link resolves '+ref,target.is_file() or (parts.path in future))
            if parts.fragment:
                targetparser=parser
                if target!=out/filename:
                    targetparser=Document();targetparser.feed(target.read_text('utf-8'))
                check(filename+': anchor resolves '+parts.fragment,unquote(parts.fragment) in targetparser.ids)
    check('20 main sections,107 field cards,58 control sections',len(re.findall(r'^## ',(out/'DOCUMENTACION_DATOS.md').read_text('utf-8'),re.M))==20 and len(pages['diccionario.html'].fields)==107 and len([x for x in pages['validaciones.html'].ids if re.match(r'vd\d+-',x)])==58)
    doc=(out/'DOCUMENTACION_DATOS.md').read_text('utf-8')
    check('All13 applied rule names and key provenance qualifications present',all(x in doc for x in ['ID01','EXP01','CAP01','CAT01','AGE01','DUP01','REN00','PRE00','CAP02R','CAP03R','CAP04R','CAP05R','CAP06R','1.454','419','2.934','dos sin explicar','no se declara realizada','nube de Claude']))
    check('Jev trial scope kept separate from data correction and funding',f['Jev']['funds_added']==0 and f['Jev']['model_decisions_received']==0 and f['Jev']['dataset_uploaded'] is False and f['Jev']['pilot_cases_prepared']==18 and f['Jev']['pilot_executed'] is False)
    # Test the exact shipped search callback in a minimal in-memory DOM. No browser or network.
    parser=pages['diccionario.html'];assert len(parser.scripts)==1
    queries=['','sum_insured','POLICIES_MOTOR',' audit_ ','__no_result__']+[row['column'] for row in dictionary]
    testcases=[{'query':q,'expected':[row['id'] for row in parser.fields if q.lower().strip() in row['search']]} for q in queries]
    c.dump(out/'dictionary_logic_fixture.json',{'fields':parser.fields,'script':parser.scripts[0],'cases':testcases})
    node_script='''const fs=require('node:fs'),vm=require('node:vm');const data=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let listener;const fields=data.fields.map(x=>({id:x.id,dataset:{search:x.search},hidden:false}));const input={addEventListener:(type,cb)=>{if(type!=='input')throw Error(type);listener=cb;}};const count={textContent:''};const document={getElementById:id=>id==='fieldSearch'?input:count,querySelectorAll:selector=>{if(selector!=='.field')throw Error(selector);return fields;}};vm.runInNewContext(data.script,{document});let checks=0;for(const tc of data.cases){listener({target:{value:tc.query}});const actual=fields.filter(x=>!x.hidden).map(x=>x.id);if(JSON.stringify(actual)!==JSON.stringify(tc.expected))throw Error('IDs '+tc.query);checks++;if(count.textContent!==actual.length+' de 107 campos')throw Error('count '+tc.query);checks++;}process.stdout.write(JSON.stringify({passed:checks,failed:0,cases:data.cases.length,scope:'minimal_DOM_callback_not_browser_rendering'}));'''
    js=out/'source_snapshot/verify_dictionary_logic.cjs';js.write_text(node_script,encoding='utf-8')
    node=Path('C:/Users/manol/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
    result=subprocess.run([str(node),str(js),str(out/'dictionary_logic_fixture.json')],capture_output=True,text=True,check=True)
    logic=json.loads(result.stdout);check('Shipped search callback passes all field queries in minimal DOM',logic['failed']==0 and logic['cases']==112 and logic['passed']==224)
    c.dump(out/'dictionary_logic_verification.json',logic)
    check('Originals, derived files and indexes unchanged after documentation checks',all(c.digest(c.ROOT/path)==sha for path,sha in a.readj(out/'protected_data_hashes.json').items()))
    files=[p for p in out.rglob('*') if p.is_file() and p.name not in ['documentation_verification.json','documentation_verification_failure.json']]
    result={'status':'passed_own_documentary_reconciliation','passed':len(checks),'failed':0,'checks':checks,'scope':'Source/hash/metadata/ledger/document checks; not re-execution of all historical data rules.',
        'main_sections':20,'dictionary_fields':107,'validation_controls':58,'search_logic_checks':logic['passed'],'data_changes':0,
        'real_browser_rendering_verified':False,'independent_validation':False,'verified_files':{p.relative_to(out).as_posix():c.digest(p) for p in files}}
    c.dump(out/'documentation_verification.json',result)
    print(json.dumps({k:val for k,val in result.items() if k not in ['checks','verified_files']}))


if __name__=='__main__':main(Path(sys.argv[1]).resolve())
