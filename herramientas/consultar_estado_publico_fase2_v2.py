"""Concilia cuota y recibos públicos de la propia cuenta; no muta la competición."""
from pathlib import Path
import hashlib
import importlib.util
import json

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
source = R / 'herramientas/consultar_estado_publico_fase2.py'
spec = importlib.util.spec_from_file_location('read_public_v2', source)
b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
b.OUT = R / 'privado/semana2/mision017_fase2/estado_publico_20261026_v2'

if __name__ == '__main__':
    b.main()
    path = b.OUT / 'source_manifest.json'
    path.write_text(json.dumps({'read_only_source': str(source), 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'wrapper_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'private_score_not_read': True,
        'no_new_submission': True}, indent=2), encoding='utf8')
