# Tabla pública y métodos de cálculo

Referencia aportada por el participante el 16 de octubre de 2026, America/Bogota. Se transcriben las cuatro filas visibles de [la captura](captura.png), conservada con su hash en [captura.json](captura.json). La fecha de toma y el momento de cada envío son desconocidos: «3h» y «2d» se conservan como textos relativos. No se consultó la tabla en vivo. La asociación con la parte 1 procede del contexto del proyecto; la imagen no muestra título ni URL.

| Puesto visible | Equipo o archivo | D² público | Envíos | Último visible | Brecha hasta RiskForge | D² − GLM | Reducción de desviación frente al GLM |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: |
| 1 | RiskForge | 0.11416 | 3 | 3h | 0.00000 | +0.00853 | +0.9537% |
| Referencia (sin puesto) | sandbox_2_basic_glm.csv | 0.10563 | 1 | 2d | 0.00853 | +0.00000 | +0.0000% |
| Referencia (sin puesto) | sample_submission.csv | 0.07169 | 1 | 2d | 0.04247 | -0.03394 | -3.7949% |
| Referencia (sin puesto) | sandbox_1_average_cost_baseline.csv | 0.07169 | 1 | 2d | 0.04247 | -0.03394 | -3.7949% |

Los cálculos usan los scores mostrados, redondeados a cinco decimales. Las brechas son aproximaciones al resultado del servidor. Los iconos de referencia no se convierten en posiciones 2, 3 y 4. «Entries» cuenta envíos mostrados, no modelos distintos. No se identifica RiskForge como equipo propio ni se atribuyen sus envíos al participante.

## Cómo se calculan las comparaciones

Sea `s_A` el D² del candidato y `s_B` el de la referencia, evaluados sobre las mismas etiquetas, filas, pesos y definición de desviación. Según [scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.d2_tweedie_score.html), D² expresa la fracción de desviación Tweedie explicada. No mide el porcentaje de predicciones acertadas.

```text
d_1.5(y,m) = 4*(y/sqrt(m) - 2*sqrt(y) + sqrt(m))
D_modelo = sum(w_i*d_1.5(y_i,m_i))
media_y = sum(w_i*y_i)/sum(w_i)
D_nulo = sum(w_i*d_1.5(y_i,media_y))
s = 1 - D_modelo/D_nulo

Desviación normalizada = 1 - s
Brecha hasta el líder visible = s_líder - s
Diferencia de D² frente a referencia = s_A - s_B
Razón de desviaciones A/B = (1-s_A)/(1-s_B)
Reducción relativa de desviación frente a B (%) = 100*(s_A-s_B)/(1-s_B)
```

Estas relaciones de desviación requieren un mismo denominador nulo positivo. Si cambia el conjunto, la etiqueta o los pesos, no se obtiene una comparación de pérdidas válida a partir de dos scores aislados. La desviación absoluta no puede recuperarse de esta captura. La fórmula unitaria corresponde a potencia 1,5, `y>=0` y `m>0`; los pesos deben ser no negativos con suma positiva. Un objetivo completamente cero produce denominador nulo y exige tratamiento explícito. La [documentación de desviación Tweedie](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.mean_tweedie_deviance.html) fija el dominio; el código completo del scorer del concurso sigue sin verificarse.

RiskForge supera al GLM visible en `0.11416 - 0.10563 = 0.00853` de D². Bajo el denominador común, su reducción de desviación es `100*0.00853/0.89437 ≈ 0.9537%`. Frente a la referencia de coste medio, la diferencia es `0.04247` y la reducción de desviación es aproximadamente `4.57498%`. El aumento relativo del número D², `100*(s_A-s_B)/s_B`, es otra operación: no debe presentarse como reducción del error.

Las dos filas con 0,07169 empatan a la precisión mostrada. Esto no demuestra que sus predicciones sean iguales ni que compartan método. La referencia de coste medio obtiene un D² positivo; no debe confundirse con la media de las etiquetas ocultas usada en el denominador, cuyo D² sería cero.

## Qué se conoce del cálculo de las predicciones

| Fila visible | Evidencia disponible | Método que puede documentarse |
| --- | --- | --- |
| RiskForge | Nombre, puesto 1, score y tres envíos | Método desconocido; faltan código, variables, objetivo y predicciones |
| sandbox_2_basic_glm.csv | Nombre que sugiere GLM básico | No se verificaron distribución, enlace, exposición, variables o calibración |
| sample_submission.csv | Nombre de plantilla | La captura no permite conocer cómo se generaron sus valores |
| sandbox_1_average_cost_baseline.csv | Nombre que sugiere coste medio | No se verificaron agrupación, ponderación ni tratamiento de duración |

Los nombres orientan la lectura, pero no reproducen los métodos. Para las referencias propias se mantiene [la metodología actuarial](../METODOLOGIA_ACTUARIAL.md): coste de periodo `m=e*q`; tasa de cartera por ramo `sum(Y)/sum(e)`; tasa constante que minimiza la desviación de importes a potencia 1,5 `sum(Y/sqrt(e))/sum(sqrt(e))`; calibración de balance `sum(Y)/sum(m)` y calibración Tweedie `sum(Y/sqrt(m))/sum(sqrt(m))`. Se ajustan con datos del bloque autorizado y se evalúan fuera de él. Estas fórmulas propias no se atribuyen a los archivos de la captura.

El D² global se calcula concatenando las filas de los ramos, sin promediar sus D². Se mantiene la validación V22/V23/V24 y la política D29: el score público es un contraste adicional; esta imagen no justifica cambiar las etiquetas, los modelos ni los cortes. El runner de entrenamiento no queda adaptado al concurso por añadir esta tabla.

## Reproducción y alcance

Desde `C:/dev/Hakaton`:

```powershell
& '.\Preparación\.venv\Scripts\python.exe' '.\Hackaton\Semana 1\Modelado\Referencias_publicas\calcular.py'
```

[calcular.py](calcular.py) genera esta tabla y [calculos.json](calculos.json) desde la transcripción y [la plantilla de métodos](metodos.md), con aritmética decimal. La evidencia de comprobación se conserva en el cierre D64. La operación solo registra y compara resultados visibles; no recalcula scores públicos desde predicciones ocultas. IA: transcripción, derivación y comprobación propia. Revisión humana e independencia no acreditadas. Aplican Documentación IAA §2 y §§4–6, Gobernanza §2.8 y Consideraciones profesionales §§3.5–3.6 para procedencia y límites.
