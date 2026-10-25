"""Escribe manifiesto.json de la verificación nocturna: huellas de entradas (corridas de Codex, base, dev3, F0, pólizas y siniestros, tabla de capital), scripts, salidas y documentos; incluye las corridas de B20 (atribución, contracción, bandas, incendio/AD y síntesis)."""
import hashlib
import json
import pathlib
import sys

D = pathlib.Path(__file__).resolve().parent
RAIZ = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path('/mnt/user-data/uploads/Hakaton/Hackaton/Repositorio_IAA2026/privado/semana2')
CAPITAL = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path('/home/claude/s2dec/final_privado/capital_caps2_01.parquet')


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


entradas = {}
for run in ['dev5_20261023T232328Z_69df9ead', 'dev6_20261023T234239Z_fdab9f0b', 'dev7_20261023T235935Z_55507793', 'cola_20261024T001114Z_e5d1c211', 'mecanismo_20261024T002849Z_c8f124bf',
            'mezcla_20261024T004833Z_e8ff18e0', 'soporte_20261024T010555Z_c4428b52', 'coberturas_20261024T011932Z_14b50ca9', 'revision_filas_20261023T235757Z_cafaba7d', 'dev3_20261023T181613Z_24c943a3',
            'dev8_20261024T013001Z_e8a35214', 'ridge20_20261024_v1', 'estabilidad_b19_20261024T014815Z_9b2b1803', 'traza_b19_20261024T021036Z_fe5038de',
            'b20_atribucion_20261024_v1a', 'contraccion_b20_20261024T023428Z_7f3565db', 'b20_bandas_calibracion_20261024_v1', 'incendio_AD_b20_20261024T025027Z_87782526', 'b20_sintesis_20261024_v1']:
    for p in sorted((RAIZ / 'desarrollo2023' / run).rglob('*')):
        if p.is_file():
            entradas[f'desarrollo2023/{run}/{p.relative_to(RAIZ / "desarrollo2023" / run).as_posix()}'] = sha(p)
for n in ['target_T0_and_stresses.parquet', 'partitions.parquet']:
    entradas[f'preparacion/base_20261023T164102Z_b3e6c2a3/{n}'] = sha(RAIZ / 'preparacion' / 'base_20261023T164102Z_b3e6c2a3' / n)
for l in ['motor', 'buildings', 'contents']:
    entradas[f'ultimo/f0_ultimo_20261023T170841Z_82038766/F0_{l}.parquet'] = sha(RAIZ / 'ultimo' / 'f0_ultimo_20261023T170841Z_82038766' / f'F0_{l}.parquet')
entradas['decisiones_participante_20261023/capital_caps2_01.parquet'] = sha(CAPITAL)
entradas['preparacion/base_20261023T164102Z_b3e6c2a3/claim_assignment_audit.parquet'] = sha(RAIZ / 'preparacion' / 'base_20261023T164102Z_b3e6c2a3' / 'claim_assignment_audit.parquet')
EMERGING = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 else pathlib.Path('/mnt/user-data/uploads/Hakaton/Hackaton/Semana 2/Datos/emerging')
for l in ['motor', 'buildings', 'contents']:
    entradas[f'emerging/policies_{l}.parquet'] = sha(EMERGING / f'policies_{l}.parquet')
entradas['emerging/claims.parquet'] = sha(EMERGING / 'claims.parquet')
scripts = {n: sha(D / n) for n in ['verificar_nocturna.py', 'figuras_nocturna.py', 'verificar_informe.py', 'completar_manifiesto.py']}
salidas = {n: sha(D / n) for n in ['evidencia_nocturna.json', 'tablas/controles.csv', 'tablas/recetas_recalculadas.csv', 'tablas/pares_recalculados.csv', 'tablas/remuestreo_pares.csv', 'tablas/remuestreo_L1.csv',
                                   'tablas/recetas_b19_b20.csv', 'tablas/pares_b19_b20.csv', 'tablas/remuestreo_b19_b20.csv', 'tablas/retiros_037.csv', 'tablas/hessianos_b19.csv', 'tablas/influencia_local_destacados.csv',
                                   'tablas/ganancia_acumulada_b20.csv', 'tablas/bandas_b20.csv',
                                   'fig1_concordancia.png', 'fig2_credibilidad.png', 'fig3_folds.png', 'fig4_b19_b20.png', 'fig5_influencia.png', 'fig6_atribucion_bandas.png']}
documentos = {n: dict(sha256=sha(D / n), bytes=(D / n).stat().st_size) for n in ['INFORME.md', 'aporte_CLA-S2-20261024-007.md', 'aporte_CLA-S2-20261024-008.md', 'aporte_CLA-S2-20261024-011.md', 'aporte_CLA-S2-20261024-021.md', 'cifras_informe.json', 'verificacion_informe.json']}
m = dict(autor='Claude (Cowork)', descripcion='Verificación independiente de la tanda nocturna de Codex (solo 2023), 24 de octubre de 2026; ampliada a las unidades 028–033, 035–039 y B20-ATTR a B20-SYNTH (040–044)', entradas=entradas, scripts=scripts, salidas=salidas, documentos=documentos,
         nota='Las entradas son copias con huella de las corridas congeladas de Codex en privado/semana2; los OOF grandes no se copian a esta carpeta. verificacion_informe.json lleva la hora de su ejecución.')
(D / 'manifiesto.json').write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding='utf-8')
print(len(entradas), 'entradas;', len(scripts), 'scripts;', len(salidas), 'salidas;', len(documentos), 'documentos')
