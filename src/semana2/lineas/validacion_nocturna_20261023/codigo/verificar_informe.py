"""Comprueba que las cifras del informe salen de las evidencias (cada cifra se formatea desde su JSON y se busca en el texto)."""
import hashlib, json, pathlib, re, sys
import pandas as pd
R = pathlib.Path('/home/claude/noche'); T = (R / 'INFORME.md').read_text()
J = lambda p: json.load(open(R / p))
es = J('salidas/s2/escalera_resumen.json'); pu = J('salidas/conf/puerta_2024_resultado.json'); p1 = J('salidas/p1/p1_evaluacion.json')
pi = J('salidas/produccion/produccion_info.json'); tr = J('salidas/produccion/tendencia_opciones.json'); lg = J('salidas/s2/log_base.json')
nb = J('salidas/nb_frecuencia.json'); co = J('salidas/correccion/evaluacion_correccion.json'); ul = J('salidas/s2/ultimo_resumen.json')


def f(x, d):
    s = f'{x:,.{d}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    return s.replace('-', '−')


checks = []
def c(desc, txt):
    checks.append((desc, txt, txt in T))

c('T0 emergente', f(lg['t0_total'], 2)); c('T0 autos', f(lg['motor_t0'], 2)); c('T0 edificios', f(lg['buildings_t0'], 2)); c('T0 contenidos', f(lg['contents_t0'], 2))
for k, lab in [('L0_tasa', 'tasa'), ('L1_glm_a10', 'glm'), ('L3_gbm', 'gbm'), ('T1_glm_nivel', 't1glm'), ('T1_dev_nivel', 't1'), ('T1v2_nivel', 'A1'), ('T2v2_reg_a1', 'A2'), ('L2_fs_a1e-2', 'fs')]:
    c(f'escalera {lab} global', f(es[k]['D2_global'], 4))
    for l in ['motor', 'buildings', 'contents']:
        c(f'escalera {lab} {l}', f(es[k][f'D2_{l}'], 4))
for m in ['R0', 'A1', 'A2']:
    c(f'puerta {m}', f(pu['D2'][m], 4))
    for l in ['motor', 'buildings', 'contents']: c(f'puerta {m} {l}', f(pu['D2_por_ramo'][m][l], 4))
c('A1-R0', f(pu['pares']['A1-R0']['diff'], 4)); c('A1-R0 inf', f(pu['pares']['A1-R0']['lower'], 4)); c('A1-R0 sup', f(pu['pares']['A1-R0']['upper'], 4))
a = pu['actas'][0]['salvaguardas']
c('cliente nuevo dif', f(a['cliente_nuevo']['diff'], 4)); c('cliente nuevo lim', f(a['cliente_nuevo']['lower95'], 4)); c('influencia', f(a['influencia']['diff'], 3))
for k, lab in [('P1-L0', 'tasa'), ('P1-GLM', 'glm'), ('P1-GBMc', 'gbmc'), ('P1-GBMf', 'gbmf'), ('P1-GBMf1', 'gbmf1'), ('S30', 's30')]:
    c(f'p1 {lab}', f(p1['tabla'][k]['D2'], 4)); c(f'p1 {lab} cuerpo', f(p1['tabla'][k]['D2_cuerpo'], 4))
    if k != 'S30':
        d = p1['dif_frente_a_S30'][k]; c(f'p1 {lab} dif', f(d['diff'], 4))
c('total R0', f(pi['R0_total'] / 1e6, 2) + ' M'); c('total A1', f(pi['A1_total'] / 1e6, 2) + ' M'); c('total A1T', f(pi['A1T']['total'] / 1e6, 2) + ' M')
c('tasa NB autos', f(pi['motor']['tasa_A1_nb'], 0)); c('tasa ren autos', f(pi['motor']['tasa_A1_ren'], 0))
for l, key in [('motor', 'M'), ('buildings', 'B'), ('contents', 'C')]:
    c(f'factor tendencia {l}', f(tr[l]['factor_tendencia'], 3))
c('compl autos 2024', f(ul['motor']['2024']['comp'], 3)); c('compl edif 2024', f(ul['buildings']['2024']['comp'], 3)); c('compl cont 2024', f(ul['contents']['2024']['comp'], 3))
e24 = co['exploratorio_2024']
c('F1 2024 dif', f(e24['A1fixF1']['menos_A1'], 4)); c('F1 2024 IC', f(e24['A1fixF1']['IC90_menos_A1'][0], 4)); c('F1 2024 IC sup', f(e24['A1fixF1']['IC90_menos_A1'][1], 4))
c('b3 2024 dif', f(e24['A1fixb3']['menos_A1'], 4))
for k in ['A1fix', 'A1fixb3', 'A1fixF1']:
    c(f'total {k}', f(co['produccion'][k]['total'] / 1e6, 2) + ' M')
nbk = J('salidas/produccion/nivel_backtest.json')
pct = lambda x: (f'{100 * x:+.1f} %').replace('.', ',').replace('-', '−')
for line in ['motor', 'buildings', 'contents']:
    for w in nbk[line]:
        c(f'backtest {line} {w} E1', pct(nbk[line][w]['E1']['sesgo'])); c(f'backtest {line} {w} E3', pct(nbk[line][w]['E3']['sesgo']))
c('total A1fixF1T', f(co['produccion']['A1fixF1T']['total'] / 1e6, 2) + ' M')
# mañana del 24: sensibilidad del acta, tendencia con tope, historia neutral
ps = J('salidas/conf/puerta_sensibilidad.json'); cn = ps['cliente_nuevo']['A1']
q05 = [cn[t]['q050'] for t in ('acta_2000', 'n10000', 'n10000_otra_semilla')]; q025 = [cn[t]['q025'] for t in ('acta_2000', 'n10000', 'n10000_otra_semilla')]
c('sens cn q05 max', f(max(q05), 4)); c('sens cn q05 min', f(min(q05), 4)); c('sens cn q025 max', f(max(q025), 4)); c('sens cn q025 min', f(min(q025), 4))
c('sens margen', f(ps['margenes_sin_redondeo']['A1']['minimo'], 3)); c('sens primaria', f(ps['primaria_sin_redondeo']['A1']['lower'], 6))
tt = J('salidas/produccion/tendencia_tope.json'); p1d = lambda x: f'{100 * x:.1f}'.replace('.', ',') + ' %'
c('tend autos sin tope', '+' + p1d(tt['motor']['sin_tope']['tendencia_21_24'])); c('tend autos tope', '+' + p1d(tt['motor']['tope_250k']['tendencia_21_24']))
pt = J('salidas/correccion/produccion_tendencia_tope.json')
for k in 'MBC': c(f'factor TEN-N2 {k}', f(pt['factores_exactos'][k], 3))
c('total A1fixTc', f(pt['A1fixTc']['total'] / 1e6, 2) + ' M')
for k in 'MBC': c(f'A1fixTc {k}', f(pt['A1fixTc']['por_ramo'][k] / 1e6, 2) + ' M')
fn = J('salidas/correccion/f1_nivel.json'); e = fn['exploratorio_2024']
for l in ['motor', 'buildings', 'contents']: c(f'F1 cociente 2024 {l}', p1d(e['cociente_total_F1_frente_A1fix'][l] - 1))
c('AE A1fix autos', f(e['AE']['A1fix']['motor']['global'], 3)); c('AE F1 autos', f(e['AE']['A1fixF1']['motor']['global'], 3))
d = e['D2']['A1fixF1n']; c('F1n dif', '+' + f(d['menos_A1fix'], 4)); c('F1n IC', f'[+{f(d["IC90"][0], 4)}; +{f(d["IC90"][1], 4)}]')
c('F1 2025 autos', p1d(fn['produccion_2025']['motor']['cociente_total'] - 1)); c('F1 2025 edif', p1d(fn['produccion_2025']['buildings']['cociente_total'] - 1))
c('total A1fixF1nTc', f(fn['A1fixF1nTc']['total'] / 1e6, 2) + ' M')
# conciliación final con Codex
cc = J('salidas/conciliacion_codex.json'); sg = lambda x: ('+' if x >= 0 else '') + f(x, 4)
for k in ['W2-B00', 'W2-B10', 'W2-B14']: c(f'codex {k}', f(cc['D2_codex_reproduce_informe'][k], 5))
for par, lab in [('codex_W2-B00 − mio_L0_tasa', 'tasa'), ('codex_W2-B10 − mio_L3_gbm', 'emergente'), ('mio_T1v2_nivel − codex_W2-B10', 'A1-B10'),
                 ('mio_T1v2_nivel − codex_W2-B14', 'A1-B14'), ('mio_A1fixF1_nivel − codex_W2-B10', 'F1-B10')]:
    v = cc['pares']['completo'][par]; c(f'conc {lab}', f"{sg(v['diff'])} [{sg(v['IC90'][0])}; {sg(v['IC90'][1])}]")
    c(f'conc {lab} cuerpo', sg(cc['pares']['cuerpo'][par]['diff']))
v = cc['pares']['cuerpo']['mio_T1v2_nivel − codex_W2-B10']; c('conc A1-B10 cuerpo IC', f"[{sg(v['IC90'][0])}; {sg(v['IC90'][1])}]")
c('conc B10 AE', f(cc['segmentos']['codex_W2-B10']['AE'], 3)); c('codex sha', cc['codex_oof_sha256'][:8] + '…' + cc['codex_oof_sha256'][-8:])
# decisiones del participante (política v2) y producción designada
ae = J('salidas/conf/puerta_2024_acta_enmendada.json'); ef = J('salidas/correccion/evaluacion_final.json'); sg2 = lambda x: ('+' if x >= 0 else '') + f(x, 4)
c('acta v2 titular', 'Titular de la versión 2: A1'); assert ae['titular_v2'] == 'A1'
pa = ae['pasos'][1]['par']; c('A2-A1', f"{sg2(pa['diff'])} [{sg2(pa['lower'])}; {sg2(pa['upper'])}]")
e4 = ef['exploratorio_2024']['A1fixF1b3n']; c('final 2024 vs b3', f"{sg2(e4['menos_A1fixb3'])} [{sg2(e4['IC90_menos_A1fixb3'][0])}; {sg2(e4['IC90_menos_A1fixb3'][1])}]")
c('final 2024 vs A1', f"{sg2(e4['menos_A1'])} [{sg2(e4['IC90_menos_A1'][0])}; {sg2(e4['IC90_menos_A1'][1])}]"); c('final D2 2024', f(e4['D2'], 4))
cu = ef['exploratorio_2024_cuerpo_F1b3n_menos_b3']; c('final cuerpo 2024', f"{sg2(cu['diff'])} [{sg2(cu['IC90'][0])}; {sg2(cu['IC90'][1])}]")
c('final F1b3 total autos 2024', p1d(ef['cociente_total_F1b3_frente_b3_2024']['motor'] - 1))
pr = ef['produccion_2025']; c('final total', f(pr['total'] / 1e6, 2) + ' M CU'); c('final sha', pr['sha256'][:8] + '…' + pr['sha256'][-8:])
for k in 'MBC': c(f'final {k}', f(pr['por_ramo'][k] / 1e6, 2) + ' M')
for l in ['motor', 'buildings', 'contents']: c(f'final tasa {l}', f(pr['tasa_por_ramo'][l], 1))
c('final mediana', p1d(pr['cambio_por_fila_frente_A1fixb3']['mediana_abs'])); c('final p99', p1d(pr['cambio_por_fila_frente_A1fixb3']['p99_abs']))
import re as _re
_t = open(R / 'salidas/s2/comparacion_final_dev2023.txt').read(); _m = _re.search(r"A1fixF1b3_nivel \{[^}]*'diff': np.float64\(([-0-9.e]+)\), 'q05': ([-0-9.e]+), 'q95': ([-0-9.e]+)", _t)
c('final dev2023', f"{sg2(float(_m.group(1)))} [{sg2(float(_m.group(2)))}; {sg2(float(_m.group(3)))}]")
pc = pd.read_csv(R / 'salidas/correccion/prima_comercial_designada.csv'); c('prima designada suma', f(round(pc.prima_comercial.sum()), 0) + ' CU')
# validación antes del envío
nbr = J('salidas/correccion/nb_nivel_revision.json'); rr = nbr['fuera_de_tiempo_2023_a_2024']['A1fixF1b3']
for k in ('bruto', 'cuerpo', 'credibilidad'):
    v = rr['pares_2024'][k]; c(f'nb {k}', f"| {sg2(v['menos_sin_factor'])} | [{sg2(v['IC90'][0])}; {sg2(v['IC90'][1])}] |")
sgm = rr['segmentos']; c('nb 2023 motor', f"A/E {f(sgm['motor_2023_nuevo']['AE'], 2)} frente a {f(sgm['motor_2023_renov']['AE'], 2)}")
c('nb 2024 motor', f"({f(sgm['motor_2024_nuevo']['AE'], 2)} frente a {f(sgm['motor_2024_renov']['AE'], 2)})")
c('nb efecto 2025', f"{round(100 * nbr['agrupado_2023_24_y_2025']['motor']['efecto_en_2025']['bruto']['cambio_total_2025'])} %")
r5 = J('revision/rev5/resultados.json'); assert r5['veredicto']['listo_para_enviar'] and not r5['veredicto']['bloqueantes'] and r5['sha256_archivo'] == pr['sha256']
c('rev5 dif max', '5e-7 CU'); c('rev5 renov tardias', '2.961 renovaciones')
# conciliación con la línea ML independiente
cm = J('salidas/conciliacion_mlind.json'); mz = J('salidas/correccion/mezcla_mlind.json')
for per, key in (('dev2023_orden', 'Desarrollo'), ('hold2024_orden', '2024')):
    for k in ('T2b_neutral', 'media_neutral'):
        v = cm[per][k]; c(f'mlind {per} {k}', f"{sg2(v['menos_mio'])} [{sg2(v['IC90'][0])}; {sg2(v['IC90'][1])}]")
c('mlind cuerpo dev', f"({sg2(cm['dev2023_orden']['media_neutral']['cuerpo_menos_mio'])} y {sg2(cm['hold2024_orden']['media_neutral']['cuerpo_menos_mio'])})")
pm = cm['produccion_2025']['por_ramo_mlind_sobre_mio']; c('mlind totales', f"+{p1d(pm['M'] - 1)} en autos, +{p1d(pm['B'] - 1)} en edificios y {p1d(pm['C'] - 1).replace('-', '−')} en contenidos")
c('mezcla sha', mz['sha256'][:8] + '…' + mz['sha256'][-8:]); c('mezcla mediana', p1d(mz['cambio_por_fila_frente_designada']['mediana_abs']))
c('mlind sha', cm['produccion_2025']['sha_mlind'][:8] + '…')
_mx = pd.read_csv(R / 'datos/mlind/mezcla50_designada_mlind_2025.csv', dtype={'row_id': str})
c('mezcla bruta total', f(_mx.prediction.sum() / 1e6, 2) + ' M CU'); c('mezcla bruta sha', hashlib.sha256(open(R / 'datos/mlind/mezcla50_designada_mlind_2025.csv', 'rb').read()).hexdigest()[:8] + '…')
for k in 'MBC': c(f'mezcla bruta {k}', f(_mx.prediction[_mx.row_id.str[0] == k].sum() / 1e6, 2) + ' M')
_pe = pd.read_csv(R / 'salidas/correccion/prima_comercial_envio.csv'); c('prima envio suma', f(_pe.prima_comercial.sum(), 2) + ' CU')
c('sha envio', hashlib.sha256(open(R / 'datos/mlind/mezcla50_designada_mlind_2025.csv', 'rb').read()).hexdigest())
sd = J('salidas/sonda/diseno.json'); spre = J('salidas/sonda/preinscripcion_sonda.json'); sbt = J('salidas/sonda/backtest_2024.json')
for l in ['motor', 'buildings', 'contents']:
    c(f'sonda sigma {l}', f(sd[l]['sd_log_pub_menos_priv_2025'], 3)); c(f'sonda Z {l}', f(spre['credibilidad']['Z'][l], 3))
c('sonda ganancia', '+' + f(spre['ganancia_esperada_D2_privado'], 4)); c('sonda backtest', '+' + f(sbt['ganancia_privado_media'], 4))
c('sonda p05', '+' + f(sbt['p05_p50_p95'][0], 4)); c('sonda p95', '+' + f(sbt['p05_p50_p95'][2], 4))
rb = {k: J(f'salidas/robustez/evaluacion_{k}.json') for k in ('robcap', 'robreg', 'robglmgbm', 'robrej')}
for k, v in rb.items():
    d, e = v['desarrollo_2023'], v['exploratorio_2024']
    c(f'rob {k} dev', f"{sg2(d['diff'])} [{sg2(d['IC90'][0])}; {sg2(d['IC90'][1])}]"); c(f'rob {k} 2024', f"{sg2(e['diff'])} [{sg2(e['IC90'][0])}; {sg2(e['IC90'][1])}]")
c('rob reg cuerpo', f"({sg2(rb['robreg']['desarrollo_2023']['cuerpo'])} en 2023 y {sg2(rb['robreg']['exploratorio_2024']['cuerpo'])} en 2024)")
prb = J('salidas/robustez/produccion_robusta.json')
for per in ('desarrollo_2023', 'exploratorio_2024'):
    v = prb[per]['mezcla_nueva']; c(f'mezcla robusta {per}', f"{sg2(v['menos_mezcla_vieja'])} [{sg2(v['IC90'][0])}; {sg2(v['IC90'][1])}]")
c('mezcla robusta sha', prb['produccion']['mezcla50_robusta']['sha256'][:8] + '…'); c('mezcla robusta total', f(prb['produccion']['mezcla50_robusta']['total'] / 1e6, 2) + ' M CU')
rp = J('salidas/robustez/ruido_publico_pares.json'); v25 = J('salidas/robustez/validacion_2025.json')['pares_2024']['mezcla_robusta_menos_enviada']
c('ruido sd', f(rp['sd_diferencia_publico'], 4)); c('ruido centro', sg2(rp['diferencia_2024_completo']))
c('pesos 2025', f"{sg2(v25['con_pesos_2025'])} [{sg2(v25['IC90_con_pesos'][0])}; {sg2(v25['IC90_con_pesos'][1])}]")
# DES24, tablero y sonda de nivel global
d24 = J('salidas/robustez/des24_candidatos.json')
for l, n in d24['filas'].items(): c(f'des24 filas {l}', f(n, 0))
for k, lab in [('sinF1', 'sin historia'), ('robcap', 'C1'), ('robreg', 'C2'), ('robrej', 'C4')]:
    g_ = d24['frente_a_base']['global'][k]
    row = f"{sg2(g_['diff'])} [{sg2(g_['IC90'][0])}; {sg2(g_['IC90'][1])}] | " + ' | '.join(sg2(d24['frente_a_base'][l][k]['diff']) for l in ['motor', 'buildings', 'contents'])
    c(f'des24 fila {lab}', row)
sd_ = J('salidas/sonda_global/diseno.json'); sb_ = J('salidas/sonda_global/backtest_2024.json'); sp_ = J('salidas/sonda_global/preinscripcion.json')
cx = J('salidas/sonda_global/contexto.json')
c('perdida nivel 0.8', f(sd_['perdida_D2_por_error_de_nivel_2024']['0.8'], 4)); c('perdida nivel 1.3', f(sd_['perdida_D2_por_error_de_nivel_2024']['1.3'], 4))
c('error redondeo', f(sd_['pares']['0.85-1.20']['error_redondeo_log_max'], 4)); c('sigma', f(sd_['sigma_2025'], 4)); c('Z', f(sd_['Z'], 3))
c('tau', f(sp_['credibilidad']['tau'], 2)); c('Z prei', f(sp_['credibilidad']['Z'], 3))
for k, lab in [('nivel_como_2024', 'como 2024'), ('nivel_correcto', 'correcto'), ('nivel_x1.3', 'x1.3'), ('nivel_x0.8', 'x0.8'), ('ponderado_por_la_previa', 'previa')]:
    v = sb_[k]; c(f'backtest {lab}', f"| {sg2(v['ganancia_privado_media'])} | {sg2(v['p05_p50_p95'][0])} a {sg2(v['p05_p50_p95'][2])} | {round(v['prob_ganar'] * 100):.0f} % |")
for nm, v in sp_['sondas'].items(): c(f'sha {nm}', v['sha256'][:8] + '…')
c('tablero primero', f(cx['tablero']['equipos'][0][1], 5)); c('tablero cuarto', f(cx['tablero']['equipos'][3][1], 5))
c('distancia', f"{f(cx['tablero']['distancia_al_cuarto'], 4)} a {f(cx['tablero']['distancia_al_primero'], 4)}")
c('A/E autos 2024', f(cx['real_esperado_2024_nivel_2023']['motor'], 2)); c('A/E edificios 2024', f(cx['real_esperado_2024_nivel_2023']['buildings'], 2))
c('cuota NB', f"el 76 % de las filas es nuevo negocio, frente al {round(cx['cuota_nuevo_negocio']['2023'] * 100):.0f} % de 2023 y el {round(cx['cuota_nuevo_negocio']['2024'] * 100):.0f} % de 2024")
assert round(cx['cuota_nuevo_negocio']['2025'] * 100) == 76
rs_ = J('salidas/sonda_global/resultado.json')
c('sonda 0.85', f(rs_['d2_sondas']['0.85'], 5)); c('sonda 1.20', f(rs_['d2_sondas']['1.2'], 5))
c('beta A', f(rs_['beta_A'], 4)); c('beta B', f(rs_['beta_B'], 4)); c('c*', f(rs_['c_optimo_publico'], 4)); c('c final', f(rs_['c_final'], 4))
c('c* rango', f"entre {f(rs_['redondeo']['c_optimo_rango'][0], 4)} y {f(rs_['redondeo']['c_optimo_rango'][1], 4)}")
c('d2 previsto', f(rs_['d2_publico_previsto_final'], 5)); c('nula', f(rs_['nula_por_fila_implicita'], 1)); c('sha final', rs_['final']['sha256'][:8] + '…')
c('total final', f(rs_['final']['total'] / 1e6, 2) + ' M CU')
_f = pd.read_csv(R / 'salidas/sonda_global/final_sonda_global_2025.csv', dtype={'row_id': str})
for k in 'MBC': c(f'final {k}', f(_f.prediction[_f.row_id.str[0] == k].sum() / 1e6, 2) + ' M')
sg_ = J('salidas/sonda_segmento/diseno.json')['ganancia']
for seg, lab in [('nb', 'Nuevo negocio / renovación'), ('ramo', 'Ramo'), ('ramo_nb', 'Ramo × nuevo negocio')]:
    v = sg_[seg]; f4 = lambda x: sg2(x)
    c(f'segmento {seg}', f"| {lab} | {J('salidas/sonda_segmento/diseno.json')['envios'][seg]} | {f4(v['2024_nulo']['media'])} / {f4(v['2023_nulo']['media'])} | {f4(v['2024_como_el_año']['media'])} / {f4(v['2023_como_el_año']['media'])} | {f4(v['2024_previa']['media'])} / {f4(v['2023_previa']['media'])} |")
fails = [x for x in checks if not x[2]]
print(f'{len(checks) - len(fails)} de {len(checks)} cifras encontradas')
for d, t, _ in fails: print('NO ENCONTRADA:', d, t)
json.dump({'total': len(checks), 'ok': len(checks) - len(fails), 'fallos': [(d, t) for d, t, _ in fails]}, open(R / 'salidas/verificacion_informe.json', 'w'), indent=1, ensure_ascii=False)
sys.exit(1 if fails else 0)
