

## Privada P8: sensibilidad fuente a la duración, 26 de octubre de 2026

Codex, 2026-10-26T16:27:37.762719+00:00. La sonda preinscrita terminó sobre 64 filas futuras por ramo, elegidas sin respuestas dentro de negocio y duración. Solo se cambió exposure_model a la duración redondeada del 75% y del 50% de los días; los demás predictores, modelos y centros fuente quedaron fijos. El resultado es el cociente de relatividad anual fuente de las tres semillas.

| Ramo | Días | Mediana del cociente | P05–P95 | Mínimo–máximo | Señal material previa |
|---|---:|---:|---|---|---|
| motor | 75% | 0.9940 | 0.9294–1.0100 | 0.8756–1.0374 | False |
| motor | 50% | 0.9918 | 0.9152–1.0122 | 0.8645–1.8099 | False |
| buildings | 75% | 1.0000 | 0.8809–1.0064 | 0.7750–1.0313 | True |
| buildings | 50% | 0.9836 | 0.6365–1.0075 | 0.5579–1.0269 | True |
| contents | 75% | 0.9909 | 0.8296–1.1999 | 0.5589–1.2898 | True |
| contents | 50% | 0.9862 | 0.6555–1.2459 | 0.3897–1.6895 | True |

La dependencia es material por el criterio descriptivo previo en edificios y contenidos. En autos el agregado no activa esa bandera, pero se conserva un extremo de 1,8099 al reducir a la mitad los días. En edificios el mínimo es 0,5579 y en contenidos 0,3897. Todos los detalles por semilla, negocio y banda permanecen en los artefactos. La muestra finita no mide el impacto poblacional ni la ganancia predictiva.

Las nueve inferencias de base coinciden exactamente con las cachés originales. Se verificaron 1728 filas de inferencia primaria y, por separado, 216 filas de control mediante suma de los valores de hojas guardadas; el enrutamiento procede de la misma biblioteca. El replay de los arrays guardados fue exacto con carga de modelos prohibida. Los hashes y el número de árboles no cambiaron. El intento V1 falló en un selector de columnas de un fixture antes de inferir con datos reales; V2 conserva ese fallo y reutiliza las entradas idénticas, con el núcleo numérico sin cambios.

Esto justifica comparar una simplificación: quitar ese predictor manteniendo exposición en el offset, capacidad y semillas. No acredita doble conteo, fuga o error. La duración puede contener riesgo estacional o selección y retirarla podría empeorar. Tampoco se recalcularon T2b, miembros H1 o precios S2 para las intervenciones; no son cotizaciones alternativas. La retirada necesita una receta y una validación completas propias antes de cualquier adopción.

Cero ajustes, C0, recalibraciones, precios finales o envíos nuevos. P6 conserva su CSV y sus adversos estadísticos. B00, F3c y todas las alternativas se mantienen. 2024 está abierto y es adaptativo; no se acredita mejora privada ni revisión profesional independiente.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P8_sonda_exposicion_fuente_20261026_v2/report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P8_sonda_exposicion_fuente_20261026_v2/replay_report.json.
