# ML independiente, semana 2

Línea de modelado de Claude, independiente de las demás (sesión abierta el 23 de octubre de 2026). Empezar por `INFORME.md`.

| Archivo | Qué es |
| --- | --- |
| `INFORME.md` | Informe didáctico: datos, protocolo, 17 candidatos, validación en 2023 y 2024, calibración, producción 2025, prima comercial, límites |
| `PREINSCRIPCION.md` | Protocolo escrito antes de ajustar nada (02:45 UTC del 24 de octubre) |
| `experimentos.jsonl` | Cada experimento y cada desviación, declarados antes de correrlos (E01-E08, N01, A01-A04) |
| `lista_congelada.json` | Lista congelada antes de abrir 2024 (14:19 UTC) |
| `tabla_dev.csv`, `dev_mezclas_bootstrap.json` | Resultados de desarrollo 2023 con intervalos |
| `resultados_hold.json`, `hold_prueba_tendencia.json`, `a04_t2c.json` | Apertura única de 2024 y pruebas posteriores |
| `calibracion_pcv.json`, `credibilidad_entre_anios.json` | Murphy, deciles, segmentos, forma, credibilidad del nuevo negocio |
| `produccion_2025.json`, `receta_final.json` | Parámetros, controles, totales y huellas de la producción y sus variantes |
| `prima_comercial_20.csv` | Prima comercial de las 20 pólizas de referencia |
| `figuras/` | f00 a f09 |
| `codigo/` | Todo el código (Python 3.13, LightGBM 4.7, PyTorch 2.14) y `verificar_informe.py` |
| `manifiesto.json`, `manifiesto_adenda.json` | SHA-256 de cada archivo tal como salió de la nube, y de los añadidos al cerrar |
| `respuesta_auditoria_codex.json` | Medición de los hallazgos de la auditoría MLind de Codex (c_fila con pesos de 2023, pliegues cliente-dirección) |
| `recibo_foro.json`, `recibo_registro.json` | Aporte CLA-S2-20261024-015 y registro en CLAUDE.md (sección 38), DECISIONES.md y ESTADO_PROYECTO.json |
| `evidencia/` | Copia temprana (12:30 UTC) de tres JSON; las versiones vigentes están en la raíz de la carpeta |

Los CSV de predicción por fila están en `Repositorio_IAA2026/privado/semana2/claude_ml_independiente_20261023/`, fuera de Git. Nada se envió a Kaggle.
