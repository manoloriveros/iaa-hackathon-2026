Codex. Cierro la prueba de nivel/contracción preinscrita en COD-S2-20261023-012 por petición del participante. El [informe](../../Repositorio_IAA2026/docs/semana2/DESARROLLO_2023_NIVEL_INFLUENCIA.md) y el [índice activo](../../Repositorio_IAA2026/registro/semana2_desarrollo2023_actual.json) conservan las tres tandas y sus snapshots.

Se reutilizaron GLM y árboles guardados de 2023, sin ajustes nuevos de estimadores base. Se aprendieron treinta factores exclusivamente en sus filas de ajuste y se guardaron sesenta adaptadores. El ancla fija el total predicho de ajuste al de B00, no al observado o al OOF. Las mezclas del 50 % estaban fijadas antes de probar. F0, T0/C0, folds, los seis comparadores y todos los periodos permanecen iguales.

| Receta | D² OOF2023 | Predicho, millones CU | A/E |
| --- | ---: | ---: | ---: |
| W2-B00: Referencia | 0.06858 | 15.614 | 0.980 |
| W2-B03: GLM, padre | 0.08672 | 14.320 | 1.068 |
| W2-B05: Boosting simple, padre | 0.07986 | 14.113 | 1.084 |
| W2-B06: B03 con nivel B00 | 0.08904 | 15.584 | 0.982 |
| W2-B07: B05 con nivel B00 | 0.08174 | 15.622 | 0.979 |
| W2-B08: 50 % B00 + 50 % B06 | 0.09318 | 15.599 | 0.981 |
| W2-B09: 50 % B00 + 50 % B07 | 0.08077 | 15.618 | 0.979 |

Mover solo el nivel acerca los totales a B00, pero B06/B07 siguen perdiendo su ventaja al retirar grupos favorables. Las contracciones B08/B09 conservan signo positivo bajo el retiro de sus propios grupos y de las listas congeladas de sus padres:

| Frente a B00 | Diferencia D² completa | Intervalo exploratorio 95 % | Tras retirar sus propios 31 favorables | Tras retirar los 31 del padre |
| --- | ---: | --- | ---: | ---: |
| W2-B06 | 0.02046 | [0.00138, 0.03877] | -0.00817 | -0.00809 |
| W2-B07 | 0.01316 | [0.00073, 0.02346] | -0.00430 | -0.00414 |
| W2-B08 | 0.02460 | [0.01468, 0.03497] | 0.00581 | 0.00587 |
| W2-B09 | 0.01219 | [0.00581, 0.01791] | 0.00119 | 0.00121 |

B08 tiene el mejor punto de esta exploración y mejora los puntos de los tres ramos y ambos segmentos de negocio. B09 sigue por debajo de B00 en nuevo negocio. Se conserva B00 y todas las alternativas B01–B09, sin promoción o equivalencia declarada. Los intervalos nuevos son positivos, pero son exploratorios de 2023 sin ajuste por búsqueda adaptativa o las 45 parejas; no son confirmación de2024. El retiro mide influencia de evaluación con modelos fijos, no robustez al reentrenamiento.

Los factores normalizan predicciones dentro del ajuste; no son calibración independiente o interna fuera de muestra, y B00 también depende de los siniestros. A/E alrededor de0,98 hereda el nivel de referencia, sin probar calibración futura, reservas o último. No se impuso A/E=1, recortaron grupos o eligieron pesos después de resultados. Las sensibilidades publicadas usan adaptadores base fijos y no sustituyen escenarios reentrenados.

Pasaron 21 casos focales y 2023 controles del comprobador separado, con solapamiento. Se reconstruyeron factores sin respuestas en su entrada, momento de ajuste, contracción/orden, padres intactos, comparadores, replay con fit bloqueado, métricas e influencia. La revisión es propia de Codex. Los bloqueos de recetas previas y los hallazgos del selector conservan sus responsables; no se cierran por este resultado.

2024 sigue cerrado por instrucción expresa. No hay ajuste, predicción o score de precios de2024/test, apertura del ledger, lista final congelada, envíos o remoto. Se recibió la evidencia de instalación del selector y el seguimiento GOV005 en el foro, sin inferir autorización de apertura o actualizar sus cierres aquí.
