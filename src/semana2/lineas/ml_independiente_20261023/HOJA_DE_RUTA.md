# Evolución propuesta del modelo (24 de octubre de 2026, 16:30 UTC)

Pedido del participante: pensar cómo debería evolucionar el modelo, desde la teoría actual de aprendizaje automático, incluida la combinación con las otras líneas. Base: la mezcla 50/50 de la designada y MLind (68,99 M CU), ya en prueba en Kaggle.

## Dónde está el error

Las mediciones de esta sesión (E09 a E12 y las anteriores, todas en `experimentos.jsonl`) dicen dos cosas:

1. **La forma ya está cerca de lo que los datos sostienen.** Todo intento de añadir estructura propia del emergente quedó dentro del ruido o empeoró:

   | Intento | Resultado en D² |
   | --- | --- |
   | Ajuste fino por boosting | +0,0009 en 2023, −0,0013 en 2024 |
   | Red residual | −0,0013 en 2023 |
   | Transformer preentrenado | −0,016 frente al árbol transferido |
   | Modelo por peligro | −0,024 |
   | Tope de pérdidas grandes | −0,003 |
   | Cuatro semillas | ±0,001 |
   | Reponderar el desarrollado hacia la cartera 2025 | −0,020 |

   Con unos 9.000 siniestros emergentes, la varianza de cualquier estructura local pesa más que el sesgo que corrige. Es lo que predicen la teoría de transferencia con pocos datos del dominio objetivo (Li, Cai y Li, 2022; Tian y Feng, 2023) y la evidencia comparada de árboles frente a redes en datos tabulares (Grinsztajn y otros, 2022).
2. **El nivel es la palanca grande.**
   - En la cartera 2025 (divergencia de Bregman sobre la mezcla), un 15 % de error en el nivel de autos cuesta unos 0,002 de D².
   - La distancia entre ignorar y aplicar el exceso del nuevo negocio de autos (27 %) cuesta 0,006.
   - En edificios, un 15 % cuesta 0,001, y su nivel histórico osciló entre 590 y 366 según el año (incendio).

## Orden propuesto

1. **Nivel con el tablero, preinscrito.** Sondas en forma cerrada como en D100 sobre la mezcla:
   - autos completo, edificios y contenidos;
   - nuevo negocio de autos por separado;
   - con credibilidad calculada sobre el ruido frente a la parte privada (lección de D103).

   La desviación típica del óptimo público estimada por la validación nocturna es 5,4 % en autos, 16 % en edificios y 9,5 % en contenidos. Autos es informativo; edificios casi no. Ganancia esperada de 0,001 a 0,006, según cuánto se aleje el nivel real. Para no sobreajustar al tablero, el tablero solo fija parámetros de nivel, con regla previa y credibilidad (Dwork y otros, 2015; Blum y Hardt, 2015).
2. **Nuevo negocio con credibilidad bayesiana empírica jerárquica.** Se reúnen ramos y años, con K calculado desde la varianza del coste por siniestro (CV cercano a 4 en autos) en lugar de K = 200. Sustituye la elección C1/C2 y sirve de previa para el punto 1.
3. **Edificios con un componente estructural de incendio.** Frecuencia con relatividades del desarrollado sobre `wildfire_index`, construcción y alarmas, y nivel por exposición con credibilidad. La validación nocturna vio que un modelo de incendio del desarrollado predice 75 incendios frente a 70 observados. Debe reducir la volatilidad del nivel del ramo.
4. **Super learner entre las tres líneas** (van der Laan y otros, 2007):
   - un mismo arnés: pliegues cliente-dirección sobre 2023-2024, el mismo T0 y la misma completitud;
   - pesos no negativos por ramo, encogidos hacia la mezcla igual;
   - miembros: designada, MLind, red residual N3 y el mejor GLM solo emergente de Codex (B10, que aporta diversidad: la reducción de error de una mezcla crece con la discrepancia entre miembros, Krogh y Vedelsby, 1995).

   Ganancia esperada de 0 a 0,002. Requiere que cada línea exporte sus OOF con esos pliegues.
5. **Temperatura de las relatividades por ramo.** Un exponente a ≈ 0,9 estimado por validación cruzada y encogido hacia 1; en la muestra vale +0,0007 a +0,0012. Ganancia pequeña.

## Fuera de la hoja de ruta, con evidencia

Ajuste fino profundo en el emergente, transformer como modelo principal, tope de pérdidas, más semillas y reponderación por desplazamiento de covariables. Los modelos fundacionales tabulares (TabPFN, Hollmann y otros, 2025) rinden en conjuntos pequeños y sin un objetivo Tweedie con exposición; no son prioridad aquí.
