Codex. Cierre de022/023, cuarta unidad nocturna. [Informe](../../Repositorio_IAA2026/docs/semana2/SENSIBILIDAD_COLA_Y_NIVEL_2023.md), [decisiones](../../Repositorio_IAA2026/privado/semana2/desarrollo2023/cola_20261024T001114Z_e5d1c211/decision_journal.json). Solo2023 y modelos estándar; B00 y catálogo previo intactos,2024cerrado.

La cola tiene dos interpretaciones. T10F conserva pesos de coste por peril y reajusta con el enlace de cola guardado. T10R renormaliza pesos al añadir masa de coste último no observada: w'_p proporcional w_p/(1−t_p), q'_p=(1−t_p)q_p, Z=sum(w_p/(1−t_p)). Por álgebra q'_mezcla=q_mezcla/Z. Los modelos estándar alpha0/constantes se transforman r'=Zr y conservan exactamente el observado e'r'=er, sin un nuevo ajuste o bootstrap duplicado.

| Modelo | D² base | D² T10F reajustado | D² T10R | Nominal base, millones CU | Nominal T10F | Nominal T10R |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| B00 | 0.06858169 | 0.06861450 | 0.06858169 | 15.7873 | 16.1475 | 16.1885 |
| B12 | 0.07491526 | 0.07492702 | 0.07491526 | 15.5441 | 15.8955 | 15.9356 |
| B14 | 0.08671008 | 0.08671999 | 0.08671008 | 15.6061 | 15.9582 | 15.9983 |

En B14, T10R aumenta el total nominal condicionado2023 unos392.261CU (+2,514%) y conserva D²/predicciones observadas (diferencia máxima1,82e-12CU). T10F sube unos352.141CU (+2,256%), pero apenas cambia D²+0,00000991 y reduce el predicho observado unos551CU. El nominal es exposición de los mismos periodos2023×tasa bajo coste completo, no precio2025/test o etiqueta observada. El score no identifica la masa de cola o escala de último. No se elige uno de estos supuestos por score.

Se guardaron seis contrastes T10F con2.000sorteos comunes y retirada31grupos. Los pequeños intervalos frente a la base quedan sobre cero en B00/B12 y cruzan cero en B14; los tres incrementos cambian de signo tras retirar sus31grupos favorables. Sus cifras completas están en el informe; ninguna promoción, retiro, equivalencia o lista final. Las seis configuraciones de sensibilidad quedan en índice específico; el catálogo común de19recetas y las171comparaciones anteriores conservan su corte. La prueba separa mecanismo de observación y familia de precio, sin reentrenar referencias por rutina.

DiezGLM nuevos/treintaconstantes;quincecopias exactas contenidos y45adaptadores algebraicos sin fit. Contadores propios100ajustesprecio/90constantes;30auxiliaresv6 separados,0curvasdereporte nuevas. El fallo de023 ocurrió después de tresconstantes/antesdeGLM: se preservaron snapshots e intento, se recuperaron dosbundles conSHA y solo se calcularon27constantes pendientes. No se cambió receta por resultados.

Pasaron715controles separados y34adversos. Los adversos tuvieron un fallo de comparación binaria racional/float de2,22e-16; se conserva33pases/1fallo y su código, se cambió a tolerancia1e-14 y solo se repitió ese caso. La identidad racional exacta ya pasaba. No se repitieron suites/ajustes/remuestreos inalterados. Verificación por otro método de curvas/pesos, óptimo escalar, gradiente, exp(Xbeta), fuentes, ámbitos, métricas/segmentos y6bootstrap por multiplicidades. Revisión técnica propia, no profesional independiente.

Masa/severidad de cola, estacionariedad, composición individual por peril y último siguen condicionados; no se declara T10R verdadero o corrector económico. Siguiente unidad: reservas0,75/1,25 con receta previa y modelos estándar. Ese reajuste aún no se hizo. Capital/clima/credibilidad mantienen condiciones anteriores.2024/test cerrados, ledger ausente;sin remoto, envíos, publicación externa, nuevoschats o delegación. No se modificaron otras automatizaciones.
