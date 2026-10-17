# Validación independiente de los ajustes y dashboard de datos

Carpeta de Claude, a solicitud del participante (16 de octubre de 2026; decisión D59 en `Preparación/DECISIONES.md`). Recalcula desde los Parquet originales cada regla aplicada a los datos (ID01, EXP01, CAP01, CAT01, AGE01, DUP01, REN00, PRE00 y la rama retrospectiva CAP02R–CAP05R, según la corrida activa de `current_retrospective_dataset.json`), la contrasta con las bitácoras y capas de Codex, y presenta datos crudos y ajustes en un dashboard bilingüe por producto.

| Archivo | Qué es |
| --- | --- |
| [INFORME.md](INFORME.md) | Informe crítico: verificación y crítica regla por regla, hallazgos y recomendaciones |
| [dashboard.html](dashboard.html) | Dashboard autocontenido (español/inglés, tema claro/oscuro); se abre con doble clic, sin red |
| `validar_ajustes.py` | Recálculo independiente; crea `runs/val_<marca>_<id>/` con `evidencia.json`, tablas CSV, copia del script y `manifest.json` |
| `construir_dashboard.py` + `plantilla_dashboard.html` | Construyen el dashboard a partir de la evidencia de la corrida vigente |
| `verificar_entrega.py` + `cifras_informe.json` | Comprobación sin pandas de hashes, cifras del informe y enlaces; escribe `verification.json` |
| `current_run.json` | Corrida revisada; repetir los scripts crea corridas nuevas y no lo sustituye |

Desde `C:\dev\Hakaton`:

```powershell
& '.\Preparación\.venv\Scripts\python.exe' '.\Hackaton\Semana 1\Validacion_ajustes_claude\validar_ajustes.py'
& '.\Preparación\.venv\Scripts\python.exe' '.\Hackaton\Semana 1\Validacion_ajustes_claude\construir_dashboard.py'
& '.\Preparación\.venv\Scripts\python.exe' '.\Hackaton\Semana 1\Validacion_ajustes_claude\verificar_entrega.py'
```

No entrena modelos, no modifica datos ni índices de Limpieza, no publica. El dashboard incrusta bitácoras y agregados derivados de los datos del concurso; se queda en el repositorio.
