"""Archiva cambios públicos y recibos breves; no modifica modelos ni reglas."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
OUT = R/'privado/semana2/mision017_fase2/consulta_publica_20261026_ascii'
OLD = ROOT/'Hackaton/Semana 2/Codex/fuentes/pages_response.json'
spec = importlib.util.spec_from_file_location('public_receipt_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)


def main():
    sys.stdout.reconfigure(encoding='utf8'); assert not OUT.exists(); OUT.mkdir()
    received = json.load(sys.stdin); old = w.read(OLD)['value']
    old = json.loads(next(x['text'] for x in old['content'] if x.get('type') == 'text'))
    old_pages = {a['name'].lower(): a['content'] for a in old['pages']}
    checks = []
    for page in received['pages']:
        same = old_pages.get(page['name'].lower()) == page['content']
        sha = hashlib.sha256(page['content'].encode()).hexdigest()
        path = None
        if not same:
            p = OUT/(page['name'].lower()+'.json'); p.write_text(json.dumps(page, ensure_ascii=False, indent=2), encoding='utf8'); path = w.rel(p)
        checks.append({'page': page['name'], 'body_sha256': sha, 'identical_to_23Oct': same,
                       'source': w.rel(OLD) if same else path})
    for name in ['topics', 'version_topic']:
        (OUT/(name+'.json')).write_text(json.dumps(received[name], ensure_ascii=False, indent=2), encoding='utf8')
    stamp = datetime.now(timezone.utc); topic = received['version_topic']['forum_topic']
    receipt = {'author': 'Codex', 'utc': stamp.isoformat(), 'status': 'public_sources_read_no_model_contract_change',
               'transport': 'ASCIIescapedJSONfrom original MCPmemory, Unicode restored by JSONdecoder; no repeated networkquery.',
               'supersedes_local_transport_failure': 'Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/consulta_publica_20261026/receipt.json',
               'competition': 'iaa-ai-assisted-hackathon-2026-part-2', 'connector': 'KaggleMCP',
               'pages': checks, 'topic_count_in_listing': int(received['topics']['total_count']),
               'new_topics_metadata': [a for a in received['topics']['topics'] if a['id'] in [752819, 752813]],
               'topic752819_read': {'first_message_id': topic['first_message_id'], 'author_type': topic['first_message']['author_type'],
                                    'comments_present': bool(received['version_topic'].get('messages') or received['version_topic'].get('comments')),
                                    'interpretation': 'Participant question about version-control/final-form format, not organizer clarification or a deadline change.'},
               'scope': 'Three official pages and all4topicmetadata; full new topic752819read. Team-join topic752813body not read as irrelevant to modeling. Older data topics metadata unchanged, no repeat payload audit.',
               'modeling_contract_change_adopted': False, 'new_fits': 0, 'new_prices': 0, 'new_submissions': 0,
               'old_source_sha256': w.sha(OLD),
               'source_hashes': {w.rel(p): w.sha(p) for p in OUT.glob('*.json')},
               'limits': 'No claim about unpublished private targets, allocation of public/private rows or unqueried pages. No rule inferred from participant question.'}
    p = OUT/'receipt.json'; p.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
    cut = R/'privado'/('corte_publico_'+stamp.strftime('%Y%m%dT%H%M%S%fZ')); cut.mkdir()
    current = {'receipt': w.rel(p), 'receipt_sha256': w.sha(p), 'utc': stamp.isoformat(),
               'modeling_contract_change_adopted': False, 'new_submissions': 0}
    w.update(R/'registro/semana2_mision_privada_actual.json', {'public_source_refresh_26Oct': current}, cut)
    phase = R/'registro/semana2_mision017_fase2_actual.json'
    w.update(phase, {'private_public_source_refresh_26Oct': current}, cut)
    state = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(state)['week_2_mission017_phase2_20261025']
    own['private_public_source_refresh_26Oct'] = current
    w.update(state, {'week_2_mission017_phase2_20261025': own}, cut)
    note = ('\n\n## Consulta pública acotada de semana2, 26 de octubre de 2026\n\nCodex, '+stamp.isoformat()+'. '
            'Corrección de transporte: el primer intento produjo mojibake por la codificación de stdin de Windows y falsos cambios de bytes. '
            'Se conserva con transport_defect.json y queda sustituido por este recibo. El JSONoriginal del MCPse retransmitió con escapesASCII, sin otra consulta externa. '
            'KaggleMCP: Evaluation, data-description y Submissions se cotejaron por contenido con la copia23oct. '
            'Resultado por página en '+w.rel(p)+'. Las discusiones nuevas se refieren a control de versiones e ingreso de un compañero. '
            'Se leyó íntegra752819: es una pregunta de participante sin respuesta del organizador en el cuerpo devuelto. '
            'No se infiere un nuevo formato o plazo. No cambia la receta, el objetivo último o la valoración. '
            'Se guardaron solo fuentes nuevas; las páginas idénticas conservan referencia anterior. '
            'No se examinó el cuerpo del tema de ingreso, no se repitieron cotejos de test y no hubo entrenamiento/precios/envíos.\n')
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, cut)
    print(json.dumps({'status': receipt['status'], 'page_comparison': checks, 'new_model_contract': False}))


if __name__ == '__main__': main()
