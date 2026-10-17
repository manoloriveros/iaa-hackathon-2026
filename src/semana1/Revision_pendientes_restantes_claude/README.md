# Revisión de los 265 capitales pendientes fuera del grupo F

Carpeta de Claude, a solicitud del participante (16 de octubre de 2026; decisión D65 en `Preparación/DECISIONES.md`). Revisa los cinco grupos de D48 que siguen pendientes en la rama retrospectiva además del grupo F (revisado en D63): otros conflictos de capital, riesgo o distancia temporal (138), sin referencia original habitual (108), dependientes de interpretar T/W (16), apoyo dependiente de correcciones CAP01 (2) y la discrepancia C48613718 (1). Recalcula desde los originales la historia y todas las referencias de cada póliza, clasifica el motivo por el que cada fila no cumple D34, mide en todo el archivo los comportamientos que permiten interpretarlo (mudanzas, ampliaciones a mitad de año, alias t/w) y deja cinco criterios con listas congeladas sin aplicar (MOV01-R, END01-R, END02-R, TW01-R, CHAIN01-R) más una propuesta de modelado para las 149 filas sin referencia. No modifica datos, índices ni corridas de Codex.

| Archivo | Qué es |
| --- | --- |
| [INFORME.md](INFORME.md) | Comportamientos del archivo, lectura de cada grupo, casos, propuestas y límites |
| [informe.html](informe.html) | Informe interactivo con explorador de las 265 filas (historia completa, referencias, siniestros, póliza vecina); se abre con doble clic, sin red |
| `revisar_pendientes_restantes.py` | Recálculo independiente; crea `runs/rest_<marca>_<id>/` con `evidencia.json`, nueve tablas CSV, copia del script y `manifest.json` |
| `construir_informe.py` | Construye `informe.html` a partir de la corrida vigente |
| `verificar_entrega.py` + `cifras_informe.json` | Comprobación sin pandas de hashes, cifras del informe y enlaces; escribe `verification.json` |
| `current_run.json` | Corrida revisada; repetir los scripts crea corridas nuevas y no lo sustituye |

Desde `C:\dev\Hakaton`:

```powershell
& '.\Preparación\.venv\Scripts\python.exe' '.\Hackaton\Semana 1\Revision_pendientes_restantes_claude\revisar_pendientes_restantes.py'
& '.\Preparación\.venv\Scripts\python.exe' '.\Hackaton\Semana 1\Revision_pendientes_restantes_claude\construir_informe.py'
& '.\Preparación\.venv\Scripts\python.exe' '.\Hackaton\Semana 1\Revision_pendientes_restantes_claude\verificar_entrega.py'
```

Las listas de `runs/<corrida>/tables/candidatas_NO_APLICADAS.csv` (116 filas, un hash por criterio en `current_run.json` y en `evidencia.json`) no están aplicadas; cualquier aplicación necesita autorización expresa y seguiría el flujo apply/verify/finalize de Limpieza. Las 149 filas de `sin_propuesta.csv` no entran en ninguna lista de corrección.
