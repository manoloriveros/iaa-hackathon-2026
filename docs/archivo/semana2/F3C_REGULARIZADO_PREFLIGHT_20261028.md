# F3c-R: optimizador comprobado y producción de entradas por ámbito

Codex, 28 de octubre de 2026. Continúa la propuesta autorizada. El optimizador restringido y su selector pasan los controles sintéticos. La conciliación de entradas reales detectó una dependencia que impide ajustar el calibrador directamente sobre los raw completos guardados. Se implementó y registró el productor de fuente por ámbito; su estado de ejecución está separado de los resultados predictivos, todavía inexistentes.

## Qué quedó comprobado

Las 50.094 filas de 2023 pertenecen a 30.869 grupos. Los folds guardados son coherentes por cliente, dirección y grupo. Se guardaron claves exactas y hashes para los dieciséis ámbitos terminales. Al cerrar sus dependencias se necesitan también diez ámbitos de base con tres folds excluidos: veintiséis conjuntos únicos en total, entre 19.730 y 50.094 filas. Esto amplía el inventario de entradas, no la rejilla de modelos candidatos.

Los árboles A1 históricos se entrenan en el mercado desarrollado, pero sus curvas de completitud se estimaron con un pool que incluye siniestros emergentes de 2023. Por eso los raw de la fuente completa no son automáticamente independientes de los retenidos internos emergentes. Hay siniestros protegidos en ese ancestro en los quince ámbitos terminales propios y en los veinticinco ámbitos propios de todo el grafo. La independencia no se obtiene quitando una etiqueta del DataFrame final.

Los dieciocho modelos del ámbito completo y los quince modelos N0/semilla11 de folds individuales son candidatos a reutilización por argumentos exactos. Faltan las demás combinaciones de ámbito, familia y semilla. Los objetos de P67/P84 no se adoptan por compartir un nombre de fold: pertenecen a otra arquitectura y deben cumplir todos los contratos de origen y grupos. T2b tiene curvas fuente desarrolladas, pero sus pesos, niveles y C1 destino también deben aprenderse en el ámbito correcto.

## Optimizador y selector

Se implementó la pérdida propuesta, con seis interceptos y cuatro intensidades activas; las dos intensidades de edificios permanecen en cero. L-BFGS-B respeta los límites 0..1. Las columnas sin soporte se fijan a cero y no se recortan silenciosamente predictores o precios para ocultar fallos numéricos.

En 900 filas artificiales se hicieron 36 ajustes sintéticos, incluidos el selector de cinco folds y su control adverso, un control positivo, un segundo optimizador SLSQP, cambio de moneda y ausencia de una celda. Pasaron 17 controles. El mayor residuo KKT de los ajustes primarios fue 1,76e-8, por debajo del límite registrado de 1e-6; los dos optimizadores coinciden en el objetivo dentro de 1,23e-15.

Alterar todo el payload retenido antes del selector conservó exactamente la elección y los parámetros. Cambiar costes de entrenamiento sí los cambió. El replay JSON, la cotización individual y la permutación coinciden con ajuste bloqueado. Entradas inválidas y grupos compartidos se rechazan. Estos controles cubren el calibrador con b y z sintéticos ya formados; no prueban por sí solos la construcción real de esas entradas.

## Producción registrada

El nuevo productor filtra siniestros por las claves permitidas antes del cálculo de curvas. El corte interno de fuente excluye su fold0 desarrollado; el corte emergente excluye todos los folds del ámbito, no solo uno. Conserva las definiciones históricas de curvas, variables, semillas, early stopping y entrenamiento. El límite de peso histórico del cálculo de completitud se mantiene como parte de ese estimador; no se limita T0 para evaluar precios.

Antes de entrenar fuente se exige reproducir las curvas del ámbito completo y comprobar invariancia bajo alteración de siniestros excluidos en los veintiséis ámbitos. Después se calcula la huella completa de entradas de cada modelo y se reutiliza únicamente si coincide. Los modelos terminados y los checkpoints de early stopping se preservan.

El presupuesto registrado es de hasta 900 invocaciones nativas primarias nuevas; se reduce a 870 si los quince pares N0 históricos de folds individuales coinciden exactamente. Cada par incluye selección de iteraciones y ajuste completo. Además, hay 52 bundles de curvas primarios y 52 adversos separados. Son límites de coste, no trabajo ya terminado ni una estimación de duración. El registro distingue llamadas a curvas, ajustes nativos, controles y objetos reutilizados.

La cola local espera la admisión completa de curvas, comprueba primero la reutilización del ámbito completo y procesa los demás ámbitos de forma secuencial. Se detiene ante cualquier fallo y deja recibo para conciliar. No puntúa candidatos ni produce un CSV 2025. La producción fuente debe completarse antes de ensamblar las bases/C1/F2/factores destino y ajustar el calibrador real. Ningún estado de producción equivale a una mejora privada.

## Fallos preservados y estado

El inventario tuvo dos fallos de implementación: un selector de sufijos confundió un recibo global con uno de modelo; después, la comparación de checkpoints incluyó el índice pandas que no se serializa con `index=False`. Se conservaron los errores y versiones previas. Se corrigió la selección exacta del nombre y se verificaron valores, claves y orden con el índice de almacenamiento restablecido. Los controles sintéticos terminados no se repitieron.

La referencia F3c, R1, B00 y los resultados adversos permanecen intactos. 2024 sigue siendo desarrollo adaptativo; el corte de valoración y los maestros sin todas sus versiones temporales siguen limitando una interpretación prospectiva. No hay nuevos scores ni envíos en esta etapa.

Índice: `registro/semana2_F3c_regularizado_actual.json`. Evidencia: `privado/semana2/F3c_regularizado_20261028/preflight/scope_inventory.json`, `preflight/synthetic_optimizer.json` y `source_scoped/queue_status.json`. Los estados vivos y los recibos por ámbito tienen prioridad sobre cualquier fotografía de progreso de este informe. La revisión es propia de Codex, no validación profesional independiente.
