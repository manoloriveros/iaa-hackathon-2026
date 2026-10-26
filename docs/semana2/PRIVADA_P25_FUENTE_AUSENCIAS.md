# P25: resistencia de los árboles fuente a datos faltantes

Codex, 2026-10-26T20:34:11.415850+00:00. Los seis controles fuente pasan el margen preinscrito. Se completaron los nueve refits permitidos y se guardaron componentes históricos; todavía no se han evaluado en el algoritmo destino.

| Ramo | Vista retenida | Cambio relativo de desviación | Veto (+0,2% máximo) |
|---|---|---:|---|
| motor | native | +0.0979% | Pasa |
| motor | masked | +0.0783% | Pasa |
| buildings | native | +0.0258% | Pasa |
| buildings | masked | -0.4023% | Pasa |
| contents | native | +0.0838% | Pasa |
| contents | masked | +0.0403% | Pasa |

Vistas nativas con deterioro conservado: motor, buildings, contents. El veto admite un deterioro pequeño; pasar no equivale a mejorar. No se eligen ramos a posteriori.

La intervención añade un 10% de ausencias entre los valores observados de 16 pares campo/ramo, con claves de cliente, dirección o póliza. Mantiene parámetros, rondas y capacidad originales, etiquetas, costes y exposición. Las tres semillas se combinan geométricamente; no son validaciones independientes. Los grupos fuente de cliente/dirección se mantuvieron separados, con membresías y hashes guardados. Se comprobaron invariancia por orden y entidad, preservación de campos, guardado/carga de los modelos y suma de hojas por otro método. El replay escalar de la desviación del ensemble coincide con el resultado guardado sin ajustar ni cargar modelos para nuevas inferencias.

La evidencia sigue la distinción entre comprobación propia e independiente de Gobernanza IAA §2.8 y el registro de configuración, decisiones y límites de Documentación IAA §3, según Preparación/Antecedentes/IAA_IA/PRACTICAS_PRIORITARIAS.md.

Este único holdout ya intervino en la elección de rondas del modelo original y usa un enlace de observación fuente congelado; es una comprobación condicional y adaptativa. No demuestra que la ausencia real sea aleatoria, que desaparezca el cambio de población o que mejore la privada. Se conservan los adversos de ciclo26 y P14/P15; no se rescata un ramo o semilla favorable.

Ajustes fuente nuevos: 18. Normalizadores relativos nuevos calculados con covariables fuente: 9. Los offsets originales se reutilizan. Cero ajustes C0, calibraciones o scores destino, inferencias2025, precios finales y envíos. B00/F3c y todas las alternativas se conservan.2024 permanece abierto como desarrollo adaptativo.

Próximo trabajo: P26: prepare and preregister one complete target comparison with P25 source components in the original fixed50/50S2/H1 algorithm. Relearn only source-dependent target shapes/levels/residual stages on saved outer training groups; keep C0/N3/H1 and all global/NB/broker/influence/stress gates. First inspect the existing P17 source-swap adapter, verify complete synthetic flow and exact ancestry, and freeze code/configuration/cost before any target fit or score. Do not choose seeds, mask rates, line subsets or new mixture weights from P25. No future inference or upload before target assessment. Passing one conditional source holdout is not evidence of private generalization.

Plan: Hackaton/Repositorio_IAA2026/registro/semana2_fuente_ausencias_privada_plan.json. Resultados y replay: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P25_fuente_ausencias_20261026/report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P25_fuente_ausencias_20261026/scalar_replay.json. Código previo al ajuste:8d1a70bb. No hay validación profesional independiente ni mejora privada acreditada.
