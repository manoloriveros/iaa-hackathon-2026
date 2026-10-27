# P103: mezcla seleccionada dentro del entrenamiento

Codex, 2026-10-27T10:07:20.039147+00:00.

Queda registrada una cuadrícula fija de cinco pesos y un selector común a todos los ramos, aprendido solo con los cinco folds internos. Se comprobó el enlace de75ámbitos internos y15exteriores:180componentes propios, claves/grupos/código/datos, reporte interno y qguardados. Un ámbito erróneo se rechazó antes de cualquier aplicación. No se repitieron curvas o la auditoría numérica histórica de q.

Los componentes son anteriores a la mezcla y pueden reutilizarse en su ámbito; los factores G no pueden trasladarse a otro peso como si el cambio fuera una constante por celda. Deben reaprenderse para cada peso distinto de50/50; ese comparador debe reutilizarse exactamente. El resultado público no decide pesos, cuadrícula o umbrales.

Este paso solo valida el enlace de artefactos. El selector, sus nuevas etapas G y su flujo numérico completo todavía no están implementados o probados. Se exige preflight sintético P104, luego registro separado de evaluación real con todas las guardas y transferencia antes de cualquier CSV. Cero ajustes, aplicaciones de modelos, scores, CDF o envíos. B00 y adversos preservados,2024abierto adaptativo, fuentes/snapshots/valoración/cola y búsqueda adaptativa siguen siendo límites; sin mejora privada demostrada o revisión independiente.

Próximo: P104: implement exact finite common mixture-weight selector and full synthetic preflight per P103. Use all75saved own-inner q/scoped component caches, reuse0.5complete models; relearnGfor other weights because rowwise mixture changes are not cellwise scale changes. Verify whole outer/inner poison, objective/tie/cache parity and full replay without fitting. No real fit/score until separate evaluation registration. No grid/line/public rescue.
