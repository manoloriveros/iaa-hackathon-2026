"""Parche de la validación tras releer el foro (COD-S2-20261023-016 … COD-S2-20261024-021 y VAL04).

1. VE15: el conteo de huecos de un día en 2024→2025 alineaba por índice un concat de train y test con índices repetidos
   (en autos inflaba 20.097 a 20.110). Se recalcula con máscara alineada.
2. VE30: valor constante de compulsory_excess por ramo (250 autos, 350 edificios, …) y en el desarrollado.
3. VE31: cuota de NCB > carnet en el desarrollado, calculada aquí (en vez de citar la semana 1 de memoria).
4. VE42: lista de los netos por encima del capital (ramo, peligro, estado, neto, capital), sin row_id.
5. VE12: colisiones de row_id, policy_id y claim_id entre mercados (DAT de VAL04) y constancia de que esta validación
   nunca cruza mercados por esas claves.
6. VE28: qué variables pasarían el umbral 0,80 solo con 2023–2024 y cuáles con los dos pares (selección de CLIMA-S2-01).
Se aplicó igual a las dos copias del script antes de publicar; se conserva como constancia de la corrección. Volver a
ejecutarlo sobre el script ya parcheado se detiene porque los fragmentos originales ya no existen.
"""
import pathlib
import sys

COPIAS = [pathlib.Path(__file__).resolve().parent / 'validar_datos_s2.py']

PARCHES = [
    # 1. VE15
    ("        t = pd.concat([E.pol[l], E.test[l]]).sort_values(['policy_id', 'period_start'])\n        t['fin_prev']",
     "        t = pd.concat([E.pol[l], E.test[l]]).sort_values(['policy_id', 'period_start']).reset_index(drop=True)\n        t['fin_prev']"),
    ("                      hueco_1_en_2024_2025=int(((h == 1) & (t.loc[h.index, 'period_start'].dt.year == 2025)).sum()))",
     "                      hueco_1_en_2024_2025=int(((t.hueco == 1) & (t.period_start.dt.year == 2025)).sum()))"),
    # 2. VE30
    ("    det['compulsory_excess_constante_en_desarrollado'] = bool(D.pol['motor'].compulsory_excess.nunique() == 1)\n",
     "    det['compulsory_excess_constante_en_desarrollado'] = bool(D.pol['motor'].compulsory_excess.nunique() == 1)\n"
     "    det['compulsory_excess_valor_por_ramo'] = {l2: sorted(float(x) for x in pd.concat([E.pol[l2], E.test[l2]]).compulsory_excess.unique()) for l2 in LINES}\n"
     "    det['compulsory_excess_valor_desarrollado_autos'] = sorted(float(x) for x in D.pol['motor'].compulsory_excess.unique())\n"),
    # 3. VE31
    ("               ncb_mayor_que_carnet_test=int((E.test['motor'].ncb_years > E.test['motor'].years_licensed).sum()),\n",
     "               ncb_mayor_que_carnet_test=int((E.test['motor'].ncb_years > E.test['motor'].years_licensed).sum()),\n"
     "               ncb_mayor_que_carnet_cuota=float((t.ncb_years > t.years_licensed).mean()),\n"
     "               ncb_mayor_que_carnet_desarrollado_cuota=float((D.pol['motor'].ncb_years > D.pol['motor'].years_licensed).mean()),\n"),
    # 4. VE42
    ("        det[f'{l}_neto_mayor_que_capital'] = len(sobre)\n",
     "        det[f'{l}_neto_mayor_que_capital'] = len(sobre)\n"
     "        det[f'{l}_netos_sobre_el_capital'] = [dict(peligro=str(r.peril), estado=str(r.status), neto=round(float(r.net), 2), capital=float(r.sum_insured))\n"
     "                                             for r in sobre.sort_values('net', ascending=False).itertuples()]\n"),
    # 5. VE12
    ("               clientes_compartidos_con_poliza_emergente=int(cc.customer_id.isin(usados_c).sum()))\n",
     "               clientes_compartidos_con_poliza_emergente=int(cc.customer_id.isin(usados_c).sum()))\n"
     "    dev_test = {l: read(D.folder, f'test_{l}', ['row_id', 'policy_id']) for l in LINES}\n"
     "    dev_claims = read(D.folder, 'claims', ['claim_id'])\n"
     "    det['colisiones_de_identificadores_entre_mercados'] = {\n"
     "        l: dict(row_id_entrenamiento=int(E.pol[l].row_id.isin(set(D.pol[l].row_id)).sum()), row_id_entrenamiento_filas=len(E.pol[l]),\n"
     "                row_id_test=int(E.test[l].row_id.isin(set(dev_test[l].row_id)).sum()), row_id_test_filas=len(E.test[l]),\n"
     "                policy_id=len(set(pd.concat([E.pol[l].policy_id, E.test[l].policy_id])) & set(pd.concat([D.pol[l].policy_id, dev_test[l].policy_id]))),\n"
     "                policy_id_emergentes=int(pd.concat([E.pol[l].policy_id, E.test[l].policy_id]).nunique()))\n"
     "        for l in LINES}\n"
     "    det['colisiones_de_identificadores_entre_mercados']['claim_id'] = int(E.claims.claim_id.isin(set(dev_claims.claim_id)).sum())\n"
     "    det['colisiones_de_identificadores_entre_mercados']['claim_id_emergentes'] = len(E.claims)\n"
     "    det['uso_cruzado_de_estas_claves_en_esta_validacion'] = 'ninguno: las claves solo se cruzan dentro de cada mercado; entre mercados solo se comparan atributos de clientes y direcciones con el mismo identificador'\n"),
    # 6. VE28
    ("               sequia_vs_lluvia_corr=round(float(w.dry_summer_index.corr(w.rainfall_mm)), 3),\n",
     "               sequia_vs_lluvia_corr=round(float(w.dry_summer_index.corr(w.rainfall_mm)), 3),\n"
     "               variables_con_r_2023_2024_de_0_80_o_mas=[c for c in w.columns if c not in ('address_id', 'year') and piv[(c, 2023)].corr(piv[(c, 2024)]) >= 0.80],\n"
     "               variables_con_r_en_los_dos_pares_de_0_80_o_mas=[c for c in w.columns if c not in ('address_id', 'year') and piv[(c, 2023)].corr(piv[(c, 2024)]) >= 0.80 and piv[(c, 2024)].corr(piv[(c, 2025)]) >= 0.80],\n"),
]


def main():
    for copia in COPIAS:
        s = copia.read_text(encoding='utf-8')
        for viejo, nuevo in PARCHES:
            if s.count(viejo) != 1:
                sys.exit(f'{copia}: el fragmento no aparece exactamente una vez: {viejo[:80]!r}')
            s = s.replace(viejo, nuevo)
        copia.write_text(s, encoding='utf-8')
        print('parcheado', copia)


if __name__ == '__main__':
    main()
