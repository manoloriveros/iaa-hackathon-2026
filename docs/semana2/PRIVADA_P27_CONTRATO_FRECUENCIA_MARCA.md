# P27: contrato separado de frecuencia y marca antes de otra familia

Codex, 2026-10-26T20:51:27.585742+00:00. La revisión confirma que frecuencia/severidad ya se ensayó en ciclo3, ciclo8, ciclo16y FS/FSp; no se repetirán esas recetas ni se presenta la familia como nueva. La diferencia posible es un GLM de efectos principales sobre los cuatro años y grupos actuales, usando conjuntamente los vínculos de número y coste guardados. FS/FSpusa exposición de coste en frecuencia y marca observada: su producto puede ser un proxy coherente, pero sus piezas no identifican por sí solas frecuencia y severidad últimas.

Se conciliaron las entradas de2.409.311periodos fuente con los recuentos existentes y los grupos A1S, sin reestimar una curva ni asignar siniestros de nuevo. La primera aserción comparaba por error exposición exacta con el predictor redondeado; el fallo y código se conservan. Se corrigió la columna de lectura a calendario y se comprobó el redondeo por separado, sin cambiar datos ni repetir el fixture matemático. La comprobación nueva se centra en respuesta/peso de la marca con offset, no repite calendarios o las auditorías terminadas de RKM.

| Ramo | Peril | Periodos positivos entrenamiento | Retenidos | Marca cero retenida |
|---|---|---:|---:|---:|
| motor | bodily_injury | 6030 | 1413 | 0 |
| motor | glass_hail | 12216 | 3140 | 0 |
| motor | own_damage | 36124 | 8871 | 1 |
| motor | theft | 4901 | 1179 | 0 |
| motor | third_party_prop | 25141 | 6444 | 0 |
| buildings | accidental_damage | 3044 | 752 | 0 |
| buildings | escape_of_water | 7903 | 2025 | 0 |
| buildings | fire | 871 | 234 | 0 |
| buildings | flood | 1704 | 469 | 0 |
| buildings | storm | 6066 | 1602 | 0 |
| buildings | subsidence | 1021 | 259 | 0 |
| contents | accidental_damage | 7117 | 1777 | 0 |
| contents | escape_of_water | 4254 | 1076 | 0 |
| contents | flood | 1295 | 291 | 0 |
| contents | theft | 6064 | 1477 | 0 |

Para frecuencia, respuesta N/E_N y peso E_N. Para marca, r=E_C/E_N, respuesta C/(N*r) y peso N*sqrt(r), con potencia1,5. Una marca de coste cero y número positivo se conserva. La identidad de desviación con el offset se comprobó por otro método y se incluyó el cambio de escala de la penalización: alpha_f=alpha_nominal*n_filas/sum(E_N), alpha_m=alpha_nominal*sum(N)/sum(N*sqrt(r)). Aplicar los mismos números de alpha sin ese ajuste no sería la misma función penalizada.

Las15celdas cumplen el umbral de viabilidad fuente predefinido de100periodos positivos de entrenamiento y20retenidos. Esto no añade soporte emergente ni prueba generalización privada.

La separación depende de supuestos de observación y de los siniestros aceptados al corte. La cola última y suficiencia de reservas siguen sin identificarse. Se conserva el soporte RKM hasta1.361días frente al coste empírico condicionado a1.095; no se equiparan. Cero ajustes, inferencias, scores nuevos o envíos. B00/F3c y los adversos se conservan,2024abierto adaptativo.

Próximo trabajo: P28: preregister one standard main-effects Poisson/Tweedie1.5 count/mark source model per peril on the P27current4year paired-offset contract, if the exact prior-recipe review finds no equivalent current fit. Freeze source-only preprocessing/features/regularization normalization/iteration cap and an explicit source gate/cost before fitting. Use saved global source held groups, retain zero marks and all claim/period records, no Gamma deletion or E_cost-as-count substitution. Start with source inner fits only and save each checkpoint/gradient; no full refits or new target scoring unless its preregistered source criterion passes. Keep all previous FS/FSp/cycle8/cycle16adverses; no claim this is a first count/severity family. No new C0,2025prices or upload in source stage. No P25mask tuning; private robustness and all global/NBguards remain.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P27_contrato_frecuencia_20261026/report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P27_contrato_frecuencia_20261026/synthetic_objective_identity.json.
