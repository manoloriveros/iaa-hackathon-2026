# Bases actuariales y plan de pruebas

Carpeta de Claude (Cowork), a solicitud del participante (17 de octubre de 2026; decisión D67 en `Preparación/DECISIONES.md`). Reúne el plan de pruebas de la parte 1 (metodologías en orden, expuestos, IBNR, frecuencia, severidad, coordinación de los cinco envíos diarios, pendientes y cronograma) y la primera base de cálculo sobre la capa preparada vigente: asignación de siniestros, tabla T0 por `row_id`, expuestos por ramo, año, mes y cobertura, chain-ladder de conteos por peligro con IBNR de 2024, frecuencia, severidad, reservas de caso con rango T1, prima de riesgo observada y última y referencias M00 en V22, V23 y V24. No modifica datos ni índices, no entrena modelos y no envía nada.

| Archivo | Qué es |
| --- | --- |
| [PLAN_PRUEBAS.md](PLAN_PRUEBAS.md) | El plan con sus ocho puntos y las cifras de la corrida |
| `bases_actuariales.py` | Lee `current_dataset.json`, comprueba los SHA-256 de las siete tablas usadas, calcula todo y crea `runs/bases_<marca>_<id>/` con `evidencia.json`, 21 tablas (`tables/`), copia del script y `manifest.json` |
| `verificar_entrega.py` + `cifras_plan.json` | Comprobación sin pandas de hashes, controles, capa activa y de que cada cifra del plan coincide con la evidencia; escribe `verification.json` |
| `current_run.json` | Corrida vigente; repetir el script crea corridas nuevas y no lo sustituye |

Tablas de la corrida: `asignacion_por_siniestro.parquet` y `asignacion_siniestros.csv`, `t0_por_row_id.parquet`, `expuestos_ramo_anio.csv`, `expuestos_ramo_mes.csv`, `expuestos_autos_cobertura.csv`, `retraso_reporte_cohortes.csv`, `chain_ladder_conteos.csv`, `factores_desarrollo_conteos.csv`, `completitud_2024_por_mes.csv`, `ibnr_2024_por_peligro.csv`, `ibnr_2024_por_ramo.csv`, `ibnr_por_peligro_anio.csv`, `frecuencia_ramo_anio_peligro.csv`, `frecuencia_autos_cobertura.csv`, `severidad_ramo_peligro.csv`, `reservas_caso_T1.csv`, `reservas_caso_ramo_anio.csv`, `prima_riesgo_ramo_anio.csv`, `prima_riesgo_ultima_ramo_anio.csv`, `referencias_M00.csv` y `controles.csv`.

Desde `C:\dev\Hakaton` (Windows) o desde la raíz en Linux:

```powershell
& '.\Preparación\.venv\Scripts\python.exe' '.\Hackaton\Semana 1\Bases_actuariales_claude\bases_actuariales.py'
& '.\Preparación\.venv\Scripts\python.exe' '.\Hackaton\Semana 1\Bases_actuariales_claude\verificar_entrega.py'
```

La corrida vigente se ejecutó en la máquina virtual Linux local del participante (Python 3.10.12, pandas 2.3.3, pyarrow 25.0.1) y tarda unos 40 segundos con 3 GB de memoria. Si cambia la capa activa (`current_dataset.json`), hay que repetir el script; `verificar_entrega.py` lo avisa. Las dos tablas Parquet (`t0_por_row_id` y `asignacion_por_siniestro`) son materializaciones preliminares de los entregables 1 y 2 de la metodología; el flujo de Preparación debería adoptarlas o reproducirlas con su propia verificación antes de entrenar. La corrida `bases_20261017T120043Z_d40a40af` del mismo día falló su control K18 por estar mal formulado y se conserva como historial, no como vigente.
