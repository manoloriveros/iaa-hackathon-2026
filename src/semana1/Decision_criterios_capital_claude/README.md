# Decisión actuarial sobre los criterios para los capitales pendientes

Carpeta de Claude, por delegación expresa del participante (16 de octubre de 2026; decisión D66 en `Preparación/DECISIONES.md`). El participante pidió que Claude, en rol de actuario especializado, decidiera sobre los criterios propuestos en D63 (NUL01-R) y D65 (MOV01-R, END01-R, END02-R, TW01-R, CHAIN01-R) para los 419 capitales pendientes de la rama retrospectiva y sobre el tratamiento en F0 de las 149 filas sin referencia en su póliza. La decisión autoriza los seis criterios (270 filas, incluidas las dos retenidas en D63, que se reevalúan y entran en END02-R), define PRM01-R para las 149 restantes a partir de una prueba nueva (la prima escrita por mil de capital, medida sobre todo el archivo) y fija el contrato de F0 que hace idéntica la matriz de modelado leyendo la base o la rama. No aplica nada: no modifica datos, índices ni corridas de Codex.

| Archivo | Qué es |
| --- | --- |
| [DECISION_ACTUARIAL.md](DECISION_ACTUARIAL.md) | La decisión razonada: criterio actuarial, prueba de prima, decisión por criterio, contrato de F0, orden de aplicación, límites y procedencia |
| `consolidar_decision.py` | Lee las corridas vigentes de D63 y D65, comprueba sus hashes y la rama activa, mide la prueba de prima, reevalúa las dos filas retenidas y las tres de CHAIN01-R, y escribe las listas decididas; crea `runs/dec_<marca>_<id>/` con `evidencia.json`, ocho tablas CSV, copia del script y `manifest.json` |
| `verificar_entrega.py` + `cifras_decision.json` | Comprobación sin pandas de hashes, controles, listas no aplicadas y cifras del documento; escribe `verification.json` |
| `current_run.json` | Corrida de la decisión; repetir el script crea corridas nuevas y no lo sustituye |

Tablas de la corrida: `autorizadas.csv` (270 filas con orden de aplicación, criterio, nivel, referencia y prueba de prima por fila), `prm01_F0.csv` (149 filas con las marcas de F0), `prueba_prima_global.csv`, `retenidas_D63_reevaluadas.csv`, `chain01_ancla_directa.csv`, `end01_sin_reversion.csv`, `resumen_criterios.csv` y `controles.csv`.

Desde `C:\dev\Hakaton`:

```powershell
& '.\Preparación\.venv\Scripts\python.exe' '.\Hackaton\Semana 1\Decision_criterios_capital_claude\consolidar_decision.py'
& '.\Preparación\.venv\Scripts\python.exe' '.\Hackaton\Semana 1\Decision_criterios_capital_claude\verificar_entrega.py'
```

Las listas de `runs/<corrida>/tables/` están decididas pero no aplicadas: cada criterio se aplicaría en la rama por el flujo apply/verify/finalize de Limpieza, en el orden NUL01-R, END02-R, TW01-R, MOV01-R, END01-R, CHAIN01-R y PRM01-R, con cierre y versión de protocolo. La regla de F0 (`sum_insured/1000` sobre el umbral del ramo, con `sum_insured_raw` y dos marcas `audit_*` fuera de los predictores) se incorpora a la metodología cuando se construya la matriz F0.
