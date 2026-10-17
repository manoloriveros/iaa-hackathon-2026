# Revisión de los 154 capitales pendientes con contexto incompleto

Carpeta de Claude, a solicitud del participante (16 de octubre de 2026; decisión D63 en `Preparación/DECISIONES.md`). Revisa el grupo F de D48 que sigue pendiente en la rama activa (CAP06R al revisar; las dos pólizas de D60 quedaron corregidas por D61): recalcula desde los originales la historia de cada póliza, sus referencias, los puentes de cada campo ausente y una escalera de criterios, muestra casos concretos y deja una propuesta de tratamiento (NUL01-R v1) con lista congelada de candidatas sin aplicar. No modifica datos, índices ni corridas de Codex.

| Archivo | Qué es |
| --- | --- |
| [INFORME.md](INFORME.md) | Comparación de historiales, casos, escalera de criterios y propuesta |
| [informe.html](informe.html) | Informe interactivo con explorador de las 154 filas (historia completa, referencias, puentes, siniestros); se abre con doble clic, sin red |
| `revisar_contexto_pendiente.py` | Recálculo independiente; crea `runs/ctx_<marca>_<id>/` con `evidencia.json`, diez tablas CSV, copia del script y `manifest.json` |
| `construir_informe.py` | Construye `informe.html` a partir de la corrida vigente |
| `verificar_entrega.py` + `cifras_informe.json` | Comprobación sin pandas de hashes, cifras del informe y enlaces; escribe `verification.json` |
| `current_run.json` | Corrida revisada; repetir los scripts crea corridas nuevas y no lo sustituye |

Desde `C:\dev\Hakaton`:

```powershell
& '.\Preparación\.venv\Scripts\python.exe' '.\Hackaton\Semana 1\Revision_contexto_pendiente_claude\revisar_contexto_pendiente.py'
& '.\Preparación\.venv\Scripts\python.exe' '.\Hackaton\Semana 1\Revision_contexto_pendiente_claude\construir_informe.py'
& '.\Preparación\.venv\Scripts\python.exe' '.\Hackaton\Semana 1\Revision_contexto_pendiente_claude\verificar_entrega.py'
```

La lista `runs/<corrida>/tables/candidatas_NO_APLICADAS.csv` (152 filas, hash en `current_run.json`) no está aplicada; cualquier aplicación necesita autorización expresa y seguiría el flujo apply/verify/finalize de Limpieza.
