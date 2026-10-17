"""Informe de cambios y capitales; sella los archivos de la corrida verificada."""
import base64
import html
import json
import shutil

import clean_data as c
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pyarrow.parquet as pq


def main():
    out = c.ROOT / json.loads((c.BASE / 'current_run.json').read_text(encoding='utf-8'))['workspace_relative_run']
    verification = json.loads((out / 'verification.json').read_text(encoding='utf-8'))
    assert verification['passed']
    summary = pd.read_csv(out / 'tables/change_summary.csv')
    capitals = pd.DataFrame(json.loads((out / 'capital_summary.json').read_text(encoding='utf-8')))
    plt.rcParams.update({'font.size': 10})
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.3))
    train = summary[summary.table.str.startswith('policies')]
    x = np.arange(len(train))
    axes[0].bar(x - .18, train.exposure_before, .36, label='Original')
    axes[0].bar(x + .18, train.exposure_after, .36, label='Derivada ACT/365')
    axes[0].set_xticks(x, ['Autos', 'Edificios', 'Contenidos'])
    axes[0].set_ylabel('Años de exposición, train 2021–2024')
    axes[0].set_title('Cambio del denominador'); axes[0].legend()
    for line in ['buildings', 'contents']:
        values = pq.read_table(c.RAW / f'policies_{line}.parquet', columns=['sum_insured']).column(0).to_numpy()
        axes[1].hist(np.log10(values[values > 0]), bins=90, histtype='step', label=line)
    axes[1].set_yscale('log'); axes[1].set_xlabel('log10(capital CU), importes originales')
    axes[1].set_ylabel('Filas (escala log)'); axes[1].set_title('Capitales conservados para revisión'); axes[1].legend()
    fig.tight_layout(); fig.savefig(out / 'resumen.png', dpi=150); plt.close(fig)
    parts = ['<!doctype html><html lang="es"><meta charset="utf-8"><title>Limpieza v1</title>',
        '<style>body{font:16px/1.6 system-ui;max-width:1200px;margin:40px auto;padding:0 24px;color:#182b3c}table{border-collapse:collapse;font-size:13px;display:block;overflow:auto}td,th{padding:8px;border-bottom:1px solid #ddd;text-align:right}th{background:#eaf1f6}img{max-width:100%}code{background:#edf1f4}a{color:#075b9b}</style>',
        '<h1>Limpieza de identificadores y exposición</h1>',
        '<p>Versión derivada verificable. Los once originales conservan sus hashes; solo cambian customer_id y exposure. Los capitales siguen intactos. Revisión humana pendiente; controles propios asistidos por IA.</p>',
        f'<p>Corrida: <code>{html.escape(out.name)}</code>. {verification["checks_count"]} controles técnicos satisfactorios.</p>',
        '<h2>Cambios por tabla</h2>', summary.to_html(index=False, float_format=lambda x: f'{x:,.4f}'),
        '<p>ACT/365 cuenta ambos días extremos y conserva cuatro decimales. El test no requiere corrección de exposición. Se adopta por coherencia con los datos; falta confirmación de la convención por el organizador. Las fechas permanecen iguales. Con los mismos siniestros, reducir exposición aumenta frecuencia y coste por año; no cambia por sí solo el coste esperado del periodo.</p>',
        '<img alt="Exposición antes y después, distribución de capitales" src="data:image/png;base64,' + base64.b64encode((out / 'resumen.png').read_bytes()).decode() + '">',
        '<h2>Capitales: revisión antes de decidir</h2>', capitals.to_html(index=False, float_format=lambda x: f'{x:,.2f}'),
        '<p>Los umbrales seleccionan importes altos; no son límites contractuales. Los saltos comparan periodos consecutivos, sin solapamiento, de la misma póliza. Las subidas y bajadas de mil veces apoyan investigar la escala, pero no autorizan dividir ni imputar. Algunas filas pueden cumplir varias señales.</p>']
    for line in ['buildings', 'contents']:
        queue = pd.read_parquet(out / 'tables' / f'capital_review_{line}.parquet')
        selected = queue[queue.jump_up_1000_screen].head(8)
        fields = ['table', 'row_id', 'previous_row_id', 'previous_sum_insured', 'sum_insured', 'ratio_to_previous', 'same_address_as_previous']
        parts.extend([f'<h3>Ejemplos reales: {line}</h3>', selected[fields].to_html(index=False),
                      f'<p><a href="tables/capital_review_{line}.csv">Cola completa CSV</a>. Contrastar el historial y el cambio de objeto o cobertura antes de aceptar una corrección.</p>'])
    parts.extend(['<h2>Trazabilidad y límites</h2><p>Los cambios se registran por fila en ledger, separados para cada tabla y campo, con old/new, source_row, row_id y regla. Su reversión exacta se comprobó contra el original. dataset_catalog.json identifica las seis tablas derivadas y cinco originales sin duplicarlas. Ninguna decisión de Jev intervino en la limpieza: el intento en consola no produjo respuesta por falta de saldo.</p>',
        '<p>La recuperación de claves mejora los cruces del maestro de clientes. No convierte customer_id en un factor tarifario. Estas correcciones tampoco resuelven capitales, desarrollo/IBNR, clima futuro, maestros sin historia o las 414 reclamaciones anteriores al primer periodo observado. No se entrenó ningún modelo.</p>',
        '<p><a href="rules.json">Reglas y supuestos</a> · <a href="verification.json">Verificación íntegra</a> · <a href="dataset_catalog.json">Catálogo de lectura</a> · <a href="summary.json">Resumen y convenciones</a></p></html>'])
    (out / 'informe.html').write_text('\n'.join(parts), encoding='utf-8')
    entries = [{'path': p.relative_to(out).as_posix(), 'bytes': p.stat().st_size, 'sha256': c.digest(p)}
               for p in sorted(out.rglob('*')) if p.is_file() and p.name != 'manifest.json']
    c.dump(out / 'manifest.json', {'files': entries, 'count': len(entries)})
    print(str(out / 'informe.html'))


if __name__ == '__main__':
    main()
