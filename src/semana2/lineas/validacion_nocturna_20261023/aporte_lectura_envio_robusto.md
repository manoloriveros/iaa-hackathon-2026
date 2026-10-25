Claude, sesión de validación nocturna. Lectura del envío 57602707 (mezcla robusta, D² público 0,15347 frente al 0,15390 del envío 57599788).

- No es ruido. Remuestreé 2024 por componentes al tamaño del público de 2025. La diferencia entre estas dos mezclas, que correlacionan 0,999 en logaritmo, tiene una desviación típica de 0,0004 alrededor de +0,0009, y −0,00043 es muy improbable con esa distribución (`codigo/ruido_publico_pares.py`). Lo que se ganaba en 2023–2024 no se trasladó al público de 2025.
- Tampoco lo explica la cartera. Ponderé 2024 a la mezcla de 2025 con un clasificador (AUC de 0,87 a 0,89, nuevo negocio ×5,7) y la mezcla robusta seguiría ganando +0,0016 [−0,0003; +0,0036], aunque con la quinta parte del tamaño efectivo (`codigo/validacion_2025.py`).
- Al combinar las dos evidencias, la diferencia esperada en el privado es casi nula. Para la selección final no hay motivo para preferir la robusta sobre la primera.
- La prima escrita (tarifa vigente) no añade señal: con el coeficiente estimado en 2023, el D² de 2024 baja en autos y contenidos.

Conclusión práctica: los retoques de orden del tamaño de ±0,001 no se pueden validar con 2023–2024 de forma que valgan en 2025. No conviene gastar más envíos en ellos. Verificación de IA, no revisión profesional humana.
