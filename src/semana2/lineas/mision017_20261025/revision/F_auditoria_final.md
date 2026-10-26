# Auditoría de construir_final.py (revisor F)

Se puede usar esta noche si antes se añaden tres controles; no encontré errores de lógica. El parche (`revision/F_construir_final_parcheado.py`) genera, con los recibos sintéticos, los mismos archivos (SHA b9e5a475… y ed44c04d…).

## 1. Lectura del código

- Bases: nivel con D²(F) y sondas sobre F; parábola con D²(F2) y sondas sobre F2; final sobre F2. No se mezclan.
- g: creíble f/g = acotar((c*_s/c*_g)^Z), pleno c*_s/g; misma álgebra que `resolver_celda.py`.
- Doble conteo: no lo hay. F2/F por celda es exactamente su razón de nivel y la razón de forma conserva el escalar óptimo; en la simulación, la interacción entre nivel y paso F→F2 es −0,00004 (d. t. 0,00005).
- Forma: con la a de cada sonda reproduce los seis archivos de sonda (diferencia relativa ≤ 2,2·10⁻⁶) y sus razones; el total de cada celda del final es razón × f/g.
- Parábola: con tres puntos `polyfit` interpola exacto; convexa o vértice fuera de [0,3; 1,8] → a = 1. Signo correcto (máximo de D²).
- Celdas y SHA: claves iguales a la preinscripción; los siete SHA de F2 y sondas de forma coinciden con los archivos.

Lo que falta (probado en `revision/F_sandbox`):

1. La parada preinscrita del intervalo de D²(F): con D²(F) = 0,1596 escribe un final con niveles movidos.
2. Si falta F, F2 o una sonda de nivel, o llega un SHA desconocido, se detiene con un KeyError opaco; si falta una sonda de forma, la celda queda en a = 1 sin aviso.
3. No verifica que F2 en disco sea el de las sondas ni que las razones recalculadas coincidan con `sondas_F2_info.json`.

## 2. Prueba de punta a punta con 2024

A1 de 2024 (59.202 filas), público 1/3, puntuaciones a 5 decimales; F2 y razones estimados solo con 2023; β, cuotas, σ y Z recalculados (`F_sim_e2e.py`, `F_sim_boot.py`). Ganancia del creíble frente a F2 en el privado, 200 semillas:

| Escenario | Media | p05 | p95 | P(gana) |
|---|---|---|---|---|
| Real, partición | +0,0059 | +0,0038 | +0,0073 | 1,00 |
| Real, Z de 2025 | +0,0064 | +0,0040 | +0,0082 | 1,00 |
| Nulo, bootstrap | −0,0008 | −0,0033 | +0,0013 | 0,34 |
| Nulo, partición (pesimista) | −0,0016 | −0,0042 | −0,0001 | 0,02 |

Casi todo es nivel (+0,0058); la forma suma +0,00014 y gana en el 87 %. El pleno gana +0,0071 en el real y pierde −0,0055 en el nulo. La parada «grande» saltó en 10 de 200 semillas. Acotar el vértice al rango sondeado ±0,1 no mejora (`F_sim_reglas*.json`).

Límite: el nuevo negocio de 2024 tiene 2.300–3.900 filas por celda (2025: 40.000–69.000) y A1 trae desvíos de nivel grandes, así que en 2025 cabe esperar menos ganancia.

## 3. Cambio (sustituye las líneas 63-64)

```python
    for r in json.load(open(sys.argv[1])):
        if r["sha256"] not in nombre_sha: print("AVISO: SHA desconocido, se ignora:", r["sha256"][:12]); continue
        tipo, cual = nombre_sha[r["sha256"]]; sc[tipo if cual is None else (tipo, cual)] = float(r["d2"])
    falta = ({"F", "F2"} | {("celda", s) for s in CEL if s != DED}) - set(sc)
    if falta: sys.exit(f"PARADA: faltan puntuaciones obligatorias {falta}")
    falta_forma = {("forma", (v["celda"], v["a"])) for v in SF["sondas"].values()} - set(sc)
    if falta_forma: print("AVISO: faltan sondas de forma (esa celda queda con a = 1):", falta_forma)
    lo, hi = pre["d2_F_intervalo_redondeo"]
    if sc["F"] + 5e-6 < lo - 1e-9 or sc["F"] - 5e-6 > hi + 1e-9: sys.exit(f"PARADA preinscrita: D2(F) = {sc['F']} fuera de [{lo}, {hi}]")
    assert hashlib.sha256(open("F2_ncb_previos_2025.csv", "rb").read()).hexdigest() == SF["base"]["sha256"], "F2 en disco distinto del F2 de las sondas"
    for v in SF["sondas"].values():
        cc_, a_ = v["celda"], v["a"]; rs_ = [kopt(s_.y.values[celda(s_) == cc_], aplicar(s_, {cc_: a_})[celda(s_) == cc_]) / kopt(s_.y.values[celda(s_) == cc_], s_.m.values[celda(s_) == cc_]) for s_ in ser.values()]
        assert abs(np.mean(rs_) - v["razon_nivel"]) < 6e-5, ("razón de forma distinta de la de las sondas", cc_, a_, np.mean(rs_))
```

Usar puntuaciones con 5 decimales (con 4, el redondeo domina la parábola de buildings_1 y contents_1). No seleccionar el pleno.
