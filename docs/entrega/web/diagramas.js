/* diagramas.js: diagramas SVG dibujados a mano (flujo actuarial, validación temporal, flujo de IA).
   Devuelven texto SVG; el texto se escapa. Trazos en currentColor y tokens de estilo.css. */
(function (global) {
  'use strict';
  function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
  function marcadores(id) {
    return '<defs><marker id="' + id + '" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">' +
      '<path d="M0 0 L10 5 L0 10 z" style="fill: var(--text-muted)"/></marker></defs>';
  }
  // Caja con título en negrita y líneas secundarias; centra el bloque verticalmente.
  function caja(x, y, w, h, clase, titulo, lineas, opts) {
    opts = opts || {};
    var tl = [].concat(titulo || []), sl = lineas || [];
    var alto = tl.length * 14 + sl.length * 12.5;
    var y0 = y + (h - alto) / 2 + 10;
    var s = '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" rx="7" class="' + clase + '"/>';
    var cx = opts.izquierda ? x + 10 : x + w / 2, anc = opts.izquierda ? 'start' : 'middle';
    tl.forEach(function (t, i) { s += '<text x="' + cx + '" y="' + (y0 + i * 14) + '" text-anchor="' + anc + '" class="d-t">' + esc(t) + '</text>'; });
    sl.forEach(function (t, i) { s += '<text x="' + cx + '" y="' + (y0 + tl.length * 14 + i * 12.5 + 1) + '" text-anchor="' + anc + '" class="d-s">' + esc(t) + '</text>'; });
    if (opts.num) {
      s += '<circle cx="' + (x + 13) + '" cy="' + (y + 13) + '" r="9" style="fill: var(--brand)"/>' +
        '<text x="' + (x + 13) + '" y="' + (y + 17) + '" text-anchor="middle" style="fill: #fff; font-size: 10.5px; font-weight: 700">' + opts.num + '</text>';
    }
    return s;
  }
  function flecha(id, x1, y1, x2, y2, etiqueta, ex, ey, anc) {
    var s = '<line x1="' + x1 + '" y1="' + y1 + '" x2="' + x2 + '" y2="' + y2 + '" class="d-flecha" marker-end="url(#' + id + ')"/>';
    if (etiqueta) {
      String(etiqueta).split('\n').forEach(function (ln, k) {
        s += '<text x="' + (ex !== undefined ? ex : (x1 + x2) / 2) + '" y="' + ((ey !== undefined ? ey : (y1 + y2) / 2 - 5) + k * 11.5) + '" text-anchor="' + (anc || 'middle') + '" class="d-etq">' + esc(ln) + '</text>';
      });
    }
    return s;
  }
  function ruta(id, d, etiqueta, ex, ey, anc) {
    var s = '<path d="' + d + '" class="d-flecha" marker-end="url(#' + id + ')"/>';
    if (etiqueta) String(etiqueta).split('\n').forEach(function (ln, k) {
      s += '<text x="' + ex + '" y="' + (ey + k * 11.5) + '" text-anchor="' + (anc || 'middle') + '" class="d-etq">' + esc(ln) + '</text>';
    });
    return s;
  }
  function svg(w, h, aria, cuerpo, id) {
    return '<svg class="d-svg" viewBox="0 0 ' + w + ' ' + h + '" width="' + w + '" height="' + h + '" role="img" aria-label="' + esc(aria) + '">' + marcadores(id) + cuerpo + '</svg>';
  }

  var T = {
    es: {
      flujo: {
        aria: 'Flujo actuarial en seis etapas, de los once Parquet originales al CSV verificado, con validación temporal y controles en cada paso',
        cajas: [
          [['Datos originales'], ['11 tablas · 7,8 M filas', 'nunca se modifican']],
          [['Capa preparada'], ['8 reglas reversibles', 'bitácora por fila']],
          [['Objetivo e IBNR'], ['1 siniestro → 1 periodo', 'exposición efectiva']],
          [['Variables F0–F4'], ['con fecha de acceso', 'guardia contra fugas']],
          [['10 componentes'], ['Tweedie del total y', 'frecuencia × severidad']],
          [['Mezcla y nivel 2025'], ['cortes 2023–24 y sondas', 'CSV con 10 controles']]
        ],
        val: 'Validación temporal fuera de muestra: entrenar 2021–22 → medir 2023 · entrenar 2021–23 → medir 2024',
        ctl: 'Controles automáticos y huellas SHA-256 de entradas y salidas en cada etapa (orquestador de 30 nodos para el modelo final)'
      },
      validacion: {
        aria: 'Diseño de validación temporal: tres cortes con entrenamiento en años anteriores y medición en un año posterior completo',
        filas: ['V23', 'V24', 'Producción'],
        leyenda: ['entrenamiento', 'parada y calibración (C)', 'medición (S)', 'predicción entregada'],
        nota: ['C y S: mitades de clientes de 2023 para calibrar y para medir.', 'Etiquetas valoradas al 31-12-2024: validación temporal aproximada.'],
        mitades: ['C', 'S']
      },
      ia: {
        aria: 'Flujo de trabajo asistido por IA: tres líneas publican en un foro común, un enjambre de validación audita cada seis horas y el participante decide y autoriza',
        lit: [['Literatura'], ['51 fuentes primarias', '3 papers de la IAA']],
        mcp: [['Kaggle por MCP'], ['reglas, metadatos y', 'puntuaciones (lectura)']],
        datos: [['Datos del concurso'], ['11 Parquet con SHA-256', 'auditoría con 116 gráficos']],
        lineas: [
          [['Línea de modelado'], ['estimaciones propias']],
          [['Línea creativa'], ['alternativas nuevas']],
          [['Línea de contraste'], ['réplicas y críticas']]
        ],
        foro: [['Foro común'], ['{aportes} aportes en {horas} h · hipótesis con criterio previo', 'los resultados adversos se publican igual']],
        enj: [['Enjambre de validación'], ['3 agentes: datos, modelos, gobierno', 'cada 6 h · hallazgos con criterio de cierre']],
        part: [['Participante'], ['fija prioridades, decide y autoriza', 'cada envío y cada regla de datos']],
        ctl: [['Controles automáticos'], ['45 casos × 3 entornos', 'huellas de 184 salidas']],
        pan: [['Paneles de revisión'], ['datos, validación y modelo', 'para la revisión humana']],
        ent: [['Entrega'], ['CSV verificado, informe,', 'video y repositorio']],
        etq: { publican: 'publican y\ncritican', hallazgos: 'hallazgos', propuestas: 'propuestas con evidencia', autoriza: 'encarga y autoriza', insumos: 'métodos, reglas y datos verificados', gate: 'solo si pasan' }
      }
    },
    en: {
      flujo: {
        aria: 'Six-stage actuarial pipeline, from the eleven original Parquet files to the verified CSV, with temporal validation and controls at every step',
        cajas: [
          [['Original data'], ['11 tables · 7.8 M rows', 'never modified']],
          [['Prepared layer'], ['8 reversible rules', 'row-level change log']],
          [['Target and IBNR'], ['1 claim → 1 period', 'effective exposure']],
          [['F0–F4 features'], ['with access date', 'leakage guard']],
          [['10 components'], ['Tweedie total cost and', 'frequency × severity']],
          [['Blend and 2025 level'], ['2023–24 cuts and probes', 'CSV with 10 checks']]
        ],
        val: 'Out-of-sample temporal validation: train 2021–22 → score 2023 · train 2021–23 → score 2024',
        ctl: 'Automated controls and SHA-256 fingerprints of inputs and outputs at every stage (30-node orchestrator for the final model)'
      },
      validacion: {
        aria: 'Temporal validation design: three cuts that train on earlier years and score a later full year',
        filas: ['V23', 'V24', 'Production'],
        leyenda: ['training', 'early stopping, calibration (C)', 'scoring (S)', 'delivered prediction'],
        nota: ['C and S: 2023 customer halves used to calibrate and to score.', 'Labels valued at 31-12-2024: an approximate temporal validation.'],
        mitades: ['C', 'S']
      },
      ia: {
        aria: 'AI-assisted workflow: three lines post to a shared forum, a validation swarm audits every six hours and the participant decides and authorises',
        lit: [['Literature'], ['51 primary sources', '3 IAA papers']],
        mcp: [['Kaggle via MCP'], ['rules, metadata and', 'scores (read-only)']],
        datos: [['Competition data'], ['11 Parquet with SHA-256', 'audit with 116 charts']],
        lineas: [
          [['Modelling line'], ['own estimates']],
          [['Creative line'], ['new alternatives']],
          [['Challenge line'], ['replications, critique']]
        ],
        foro: [['Shared forum'], ['{aportes} posts in {horas} h · hypotheses with prior criteria', 'adverse results are published too']],
        enj: [['Validation swarm'], ['3 agents: data, models, governance', 'every 6 h · findings with closure criteria']],
        part: [['Participant'], ['sets priorities, decides and authorises', 'every submission and data rule']],
        ctl: [['Automated controls'], ['45 cases × 3 environments', 'fingerprints of 184 outputs']],
        pan: [['Review dashboards'], ['data, validation and model', 'for human review']],
        ent: [['Delivery'], ['verified CSV, report,', 'video and repository']],
        etq: { publican: 'post and\ncritique', hallazgos: 'findings', propuestas: 'evidence-backed proposals', autoriza: 'assigns and authorises', insumos: 'verified methods, rules and data', gate: 'only if they pass' }
      }
    }
  };

  function flujo(lang, o) {
    o = o || {};
    var t = T[lang || 'es'].flujo, id = 'fa-' + (lang || 'es') + (o.filas === 2 ? '2' : '1');
    var s = '', W, H, bw, bh = 76, gap, i, x, y;
    function insignia(xx, yy, n) {
      return '<circle cx="' + xx + '" cy="' + yy + '" r="10" style="fill: var(--brand)"/>' +
        '<text x="' + xx + '" y="' + (yy + 4) + '" text-anchor="middle" style="fill: #fff; font-size: 11px; font-weight: 700">' + n + '</text>';
    }
    if (o.filas === 2) {
      W = 688; bw = 200; gap = 40;
      for (i = 0; i < 6; i++) {
        var fila = i < 3 ? 0 : 1, col = i % 3;
        x = 4 + col * (bw + gap); y = 14 + fila * (bh + 46);
        s += caja(x, y, bw, bh, i === 2 ? 'd-caja-acento' : 'd-caja', t.cajas[i][0], t.cajas[i][1]);
        s += insignia(x + 4, y + 2, i + 1);
        if (col < 2) s += flecha(id, x + bw + 3, y + bh / 2, x + bw + gap - 3, y + bh / 2);
      }
      // de la etapa 3 a la 4: baja y cruza hacia la izquierda
      var x3 = 4 + 2 * (bw + gap) + bw / 2, y3 = 14 + bh, x4 = 4 + bw / 2, y4 = 14 + bh + 46;
      s += ruta(id, 'M' + x3 + ' ' + (y3 + 2) + ' V' + (y3 + 21) + ' H' + x4 + ' V' + (y4 - 3));
      var yb = 14 + 2 * bh + 46;
      var xv0 = 4, xv1 = 4 + 2 * (bw + gap) + bw;
      s += '<path d="M' + xv0 + ' ' + (yb + 8) + ' v6 H' + xv1 + ' v-6" style="fill:none; stroke: var(--acento); stroke-width: 1.4"/>';
      s += '<text x="' + ((xv0 + xv1) / 2) + '" y="' + (yb + 28) + '" text-anchor="middle" class="d-s">' + esc(t.val) + '</text>';
      s += '<rect x="4" y="' + (yb + 38) + '" width="' + (W - 8) + '" height="24" rx="6" style="fill: rgba(235,104,52,.07); stroke: var(--acento-2); stroke-width: 1"/>';
      s += '<text x="' + (W / 2) + '" y="' + (yb + 54) + '" text-anchor="middle" class="d-s">' + esc(t.ctl) + '</text>';
      H = yb + 66;
      return svg(W, H, t.aria, s, id);
    }
    W = 820; bw = 126; gap = 11.2; y = 16;
    for (i = 0; i < 6; i++) {
      x = 4 + i * (bw + gap);
      s += caja(x, y, bw, bh, i === 2 ? 'd-caja-acento' : 'd-caja', t.cajas[i][0], t.cajas[i][1]);
      s += insignia(x + 4, y + 2, i + 1);
      if (i < 5) s += flecha(id, x + bw + 2, y + bh / 2, x + bw + gap - 2, y + bh / 2);
    }
    var xa = 4 + 3 * (bw + gap), xb = 4 + 5 * (bw + gap) + bw;
    s += '<path d="M' + xa + ' ' + (y + bh + 8) + ' v6 H' + xb + ' v-6" style="fill:none; stroke: var(--acento); stroke-width: 1.4"/>';
    s += '<text x="' + xb + '" y="' + (y + bh + 28) + '" text-anchor="end" class="d-s">' + esc(t.val) + '</text>';
    s += '<rect x="4" y="' + (y + bh + 38) + '" width="' + (W - 8) + '" height="24" rx="6" style="fill: rgba(235,104,52,.07); stroke: var(--acento-2); stroke-width: 1"/>';
    s += '<text x="' + (W / 2) + '" y="' + (y + bh + 54) + '" text-anchor="middle" class="d-s">' + esc(t.ctl) + '</text>';
    return svg(W, y + bh + 66, t.aria, s, id);
  }

  function validacion(lang) {
    var t = T[lang || 'es'].validacion, id = 'va-' + (lang || 'es');
    var W = 440, x0 = 96, cw = 68, y0 = 24, rh = 28, s = '';
    var anios = [2021, 2022, 2023, 2024, 2025];
    anios.forEach(function (a, i) { s += '<text x="' + (x0 + i * cw + cw / 2) + '" y="14" text-anchor="middle" class="d-m">' + a + '</text>'; });
    var celdas = [['E', 'E', 'CS', '', ''], ['E', 'E', 'E', 'M', ''], ['E', 'E', 'E', 'E', 'P']];
    var estilo = {
      E: 'fill: rgba(42,120,214,.16); stroke: var(--acento); stroke-width: 1',
      C: 'fill: rgba(42,120,214,.05); stroke: var(--acento); stroke-width: 1',
      M: 'fill: var(--surface-1); stroke: var(--acento-2); stroke-width: 2',
      P: 'fill: var(--acento-2); stroke: var(--acento-2); stroke-width: 1'
    };
    celdas.forEach(function (fila, r) {
      var y = y0 + r * (rh + 8);
      s += '<text x="' + (x0 - 8) + '" y="' + (y + rh / 2 + 4) + '" text-anchor="end" class="d-t">' + esc(t.filas[r]) + '</text>';
      fila.forEach(function (c, i) {
        var x = x0 + i * cw + 3, w = cw - 6;
        if (c === 'CS') {
          s += '<rect x="' + x + '" y="' + y + '" width="' + (w / 2 - 1) + '" height="' + rh + '" rx="4" style="' + estilo.C + '"/>';
          s += '<rect x="' + (x + w / 2 + 1) + '" y="' + y + '" width="' + (w / 2 - 1) + '" height="' + rh + '" rx="4" style="' + estilo.M + '"/>';
          s += '<text x="' + (x + w / 4) + '" y="' + (y + rh / 2 + 4) + '" text-anchor="middle" class="d-t">' + esc(t.mitades[0]) + '</text>';
          s += '<text x="' + (x + 3 * w / 4 + 1) + '" y="' + (y + rh / 2 + 4) + '" text-anchor="middle" class="d-t">' + esc(t.mitades[1]) + '</text>';
        } else if (c) {
          s += '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + rh + '" rx="4" style="' + estilo[c] + '"/>';
        }
      });
    });
    var yl = y0 + 3 * (rh + 8) + 4, items = [['E', t.leyenda[0]], ['C', t.leyenda[1]], ['M', t.leyenda[2]], ['P', t.leyenda[3]]];
    items.forEach(function (it, k) {
      var xl = x0 + (k % 2) * 172, yy = yl + Math.floor(k / 2) * 15;
      s += '<rect x="' + xl + '" y="' + yy + '" width="14" height="10" rx="2" style="' + estilo[it[0]] + '"/>';
      s += '<text x="' + (xl + 19) + '" y="' + (yy + 9) + '" class="d-m">' + esc(it[1]) + '</text>';
    });
    t.nota.forEach(function (ln, k) { s += '<text x="4" y="' + (yl + 46 + k * 13) + '" class="d-s">' + esc(ln) + '</text>'; });
    return svg(W, yl + 48 + t.nota.length * 13, t.aria, s, id);
  }

  function ia(lang) {
    var t = T[lang || 'es'].ia, id = 'ia-' + (lang || 'es'), en = lang === 'en';
    // Cifras vivas del foro, tomadas del mismo JSON que el resto de entregables.
    var cf = window.CIFRAS && window.CIFRAS.foro;
    t = Object.assign({}, t, { foro: [t.foro[0], [t.foro[1][0].replace('{aportes}', cf ? cf.aportes : '…').replace('{horas}', cf ? Math.round(cf.horas) : '…'), t.foro[1][1]]] });
    var W = 760, s = '';
    // Fila 1: insumos verificados
    var iw = 226, ih = 50, iy = 4;
    s += caja(4, iy, iw, ih, 'd-caja', t.lit[0], t.lit[1]);
    s += caja(267, iy, iw, ih, 'd-caja', t.datos[0], t.datos[1]);
    s += caja(530, iy, iw, ih, 'd-caja', t.mcp[0], t.mcp[1]);
    // Fila 2: tres líneas de IA con estimaciones independientes
    var ly = 84, lw = 200, lh = 42, lxs = [17, 280, 543];
    s += flecha(id, 117, iy + ih + 2, 117, ly - 3) + flecha(id, 380, iy + ih + 2, 380, ly - 3) + flecha(id, 643, iy + ih + 2, 643, ly - 3);
    s += '<text x="249" y="' + (iy + ih + 23) + '" text-anchor="middle" class="d-etq">' + esc(t.etq.insumos) + '</text>';
    lxs.forEach(function (x, i) { s += caja(x, ly, lw, lh, 'd-caja-ia', t.lineas[i][0], t.lineas[i][1]); });
    // Foro común
    var fy = 160, fx = 120, fw = 400, fh = 50;
    s += caja(fx, fy, fw, fh, 'd-caja-acento', t.foro[0], t.foro[1]);
    s += flecha(id, 117, ly + lh + 2, 190, fy - 3) + flecha(id, 380, ly + lh + 2, 330, fy - 3) + flecha(id, 643, ly + lh + 2, 490, fy - 3);
    var pl = t.etq.publican.split('\n');
    s += '<text x="146" y="' + (ly + lh + 13) + '" text-anchor="end" class="d-etq">' + esc(pl[0]) + '</text>';
    s += '<text x="146" y="' + (ly + lh + 24.5) + '" text-anchor="end" class="d-etq">' + esc(pl[1]) + '</text>';
    // Enjambre de validación: audita el foro y los artefactos cada seis horas
    var ex = 596, ey = 154, ew = 160, eh = 70;
    s += caja(ex, ey, ew, eh, 'd-caja-control', t.enj[0], [en ? '3 agents · every 6 h' : '3 agentes · cada 6 h', en ? 'data · models · governance' : 'datos · modelos · gobierno', (window.CIFRAS && window.CIFRAS.validacion_ia ? window.CIFRAS.validacion_ia.hallazgos : '…') + (en ? ' findings, closure criteria' : ' hallazgos con cierre')]);
    s += flecha(id, ex - 2, fy + fh / 2, fx + fw + 3, fy + fh / 2, t.etq.hallazgos, (ex + fx + fw) / 2, fy + fh / 2 - 7);
    // Participante: decide con la evidencia del foro y autoriza
    var px = 180, py = 244, pw = 280, ph = 50;
    s += caja(px, py, pw, ph, 'd-caja-acento', t.part[0], t.part[1]);
    s += flecha(id, 320, fy + fh + 2, 320, py - 3, t.etq.propuestas, 328, fy + fh + 20, 'start');
    s += ruta(id, 'M' + (px - 2) + ' ' + (py + ph / 2) + ' H8 V' + (ly + lh / 2) + ' H' + (17 - 3), t.etq.autoriza, 14, py + ph / 2 + 16, 'start');
    // Fila final: controles, paneles y entrega
    var by = 322, bw2 = 226, bh = 46;
    s += caja(4, by, bw2, bh, 'd-caja-control', t.ctl[0], t.ctl[1]);
    s += caja(267, by, bw2, bh, 'd-caja', t.pan[0], t.pan[1]);
    s += caja(530, by, bw2, bh, 'd-caja-acento', t.ent[0], t.ent[1]);
    s += ruta(id, 'M320 ' + (py + ph + 2) + ' V' + (by - 14) + ' H117 V' + (by - 3));
    s += flecha(id, 232, by + bh / 2, 264, by + bh / 2) + flecha(id, 495, by + bh / 2, 527, by + bh / 2);
    s += '<text x="511" y="' + (by - 6) + '" text-anchor="middle" class="d-etq">' + esc(t.etq.gate) + '</text>';
    return svg(W, by + bh + 6, t.aria, s, id);
  }

  function siniestros(lang) {
    var en = lang === 'en', id = 'si-' + (lang || 'es');
    var d = CIFRAS.datos.flujo_siniestros, t0 = CIFRAS.datos.t0;
    function n(v) { return G.fmt(v, {}, lang); }
    var cajas = [
      [[n(d.originales)], [en ? 'claims in the file' : 'siniestros en el archivo']],
      [[n(d.tras_DUP01)], [en ? 'after removing' : 'sin copias exactas', en ? 'exact copies' : '']],
      [[n(d.asignados_a_un_periodo)], [en ? 'inside the policy' : 'dentro del historial', en ? 'history' : 'de la póliza']],
      [[n(d.aceptados_asignados)], [en ? 'accepted, each in' : 'aceptados, cada uno', en ? 'exactly one period' : 'en un solo periodo']],
      [[G.fmt(t0.total_CU, { compacto: true, decM: 1 }, lang) + ' CU'], [en ? 'T0 label: incurred' : 'etiqueta T0: incurrido', en ? 'minus recoveries' : 'menos recobros']]
    ];
    var quita = [
      '−' + n(d.copias_exactas_excluidas) + (en ? ' duplicates' : ' duplicados'),
      '−' + n(d.fuera_del_historial_PRE00) + (en ? ' before history' : ' previos'),
      '−' + n(d.rechazados) + (en ? ' declined' : ' rechazados'),
      ''
    ];
    var W = 688, bw = 116, gap = 25, y = 6, h = 56, s = '';
    for (var i = 0; i < 5; i++) {
      var x = 4 + i * (bw + gap);
      var lineas = cajas[i][1].filter(function (z) { return z; });
      s += caja(x, y, bw, h, i === 4 ? 'd-caja-acento' : 'd-caja', cajas[i][0], lineas);
      if (i < 4) {
        s += flecha(id, x + bw + 2, y + h / 2, x + bw + gap - 2, y + h / 2);
        if (quita[i]) s += '<text x="' + (x + bw + gap / 2) + '" y="' + (y + h + 15) + '" text-anchor="middle" class="d-etq">' + esc(quita[i]) + '</text>';
      }
    }
    var reserva = G.fmt(t0.reserva_abiertos_CU, { compacto: true, decM: 1 }, lang);
    s += '<text x="' + (W - 4) + '" y="' + (y + h + 29) + '" text-anchor="end" class="d-m">' + esc((en ? 'includes ' : 'incluye ') + reserva + (en ? ' CU of open case reserves' : ' CU de reservas de caso')) + '</text>';
    return svg(W, y + h + 36, en ? 'From 163,150 claim records to the T0 label' : 'De 163.150 registros de siniestros a la etiqueta T0', s, id);
  }

  global.D = { flujo: flujo, validacion: validacion, ia: ia, siniestros: siniestros, T: T };
})(window);
