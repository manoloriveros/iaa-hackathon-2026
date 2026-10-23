/* figuras.js: traduce cifras_entregables.json (window.CIFRAS) en gráficos y diagramas, en español o inglés.
   Cada figura tiene un id estable; el informe, el panel y las láminas la piden por ese id. */
(function (global) {
  'use strict';
  var G = global.G, D = global.D;
  var L = {
    es: { motor: 'Autos', buildings: 'Edificios', contents: 'Contenidos', agregado: 'Agregado', publico: 'Puntuación pública (Kaggle)',
      local: 'Validación local en 2024', s30: 'Modelo final', ref: 'Tasa constante por ramo', pred: 'Predicho', obs: 'Observado',
      t0: 'Observado (T0)', t0ibnr: 'Con IBNR estimado', p2025: 'Predicción 2025', decil: 'Decil de coste predicho',
      cu: 'CU por año-exposición', ft: 'Coste total (Tweedie)', fs: 'Frecuencia × severidad', comp: 'completo', cuerpo: 'cuerpo',
      res: ['Reserva × 0,75', 'Reserva × 1', 'Reserva × 1,25'] },
    en: { motor: 'Motor', buildings: 'Buildings', contents: 'Contents', agregado: 'All lines', publico: 'Public score (Kaggle)',
      local: 'Local validation on 2024', s30: 'Final model', ref: 'Constant rate per line', pred: 'Predicted', obs: 'Observed',
      t0: 'Observed (T0)', t0ibnr: 'With estimated IBNR', p2025: '2025 prediction', decil: 'Decile of predicted cost',
      cu: 'CU per exposure year', ft: 'Total cost (Tweedie)', fs: 'Frequency × severity', comp: 'full', cuerpo: 'body',
      res: ['Reserve × 0.75', 'Reserve × 1', 'Reserve × 1.25'] }
  };
  var PELIGROS = {
    es: { bodily_injury: 'Lesiones corporales', glass_hail: 'Lunas y granizo', own_damage: 'Daños propios', theft: 'Robo', third_party_prop: 'Daños a terceros',
      accidental_damage: 'Daño accidental', escape_of_water: 'Escape de agua', fire: 'Incendio', flood: 'Inundación', storm: 'Tormenta', subsidence: 'Hundimiento' },
    en: { bodily_injury: 'Bodily injury', glass_hail: 'Glass and hail', own_damage: 'Own damage', theft: 'Theft', third_party_prop: 'Third-party property',
      accidental_damage: 'Accidental damage', escape_of_water: 'Escape of water', fire: 'Fire', flood: 'Flood', storm: 'Storm', subsidence: 'Subsidence' }
  };
  var COMP = {
    es: { CAT_motor_4s: 'CatBoost Tweedie', B_CFST_motor_tendencia: 'CatBoost Poisson × GLM gamma con tendencia', 'S04b_lgbm_F0124_F3autos': 'LightGBM Tweedie',
      S06c_lgbm_motor_red: 'LightGBM reducido', S12h_edif_md1000: 'LightGBM Tweedie', B_CFST_buildings_tendencia: 'CatBoost Poisson × sev. por capital',
      B_FSAST_buildings_tendencia: 'Aditivo × sev. por capital', S08h_hogar_F3s2: 'LightGBM Tweedie', FSA_contents: 'Aditivo × LightGBM gamma',
      FSAXc4_contents: 'Aditivo × GLM físico' },
    en: { CAT_motor_4s: 'CatBoost Tweedie', B_CFST_motor_tendencia: 'CatBoost Poisson × trended GLM gamma', 'S04b_lgbm_F0124_F3autos': 'LightGBM Tweedie',
      S06c_lgbm_motor_red: 'Reduced LightGBM', S12h_edif_md1000: 'LightGBM Tweedie', B_CFST_buildings_tendencia: 'CatBoost Poisson × sum-insured sev.',
      B_FSAST_buildings_tendencia: 'Additive × sum-insured sev.', S08h_hogar_F3s2: 'LightGBM Tweedie', FSA_contents: 'Additive × LightGBM gamma',
      FSAXc4_contents: 'Additive × physical GLM' }
  };
  var RAMOS = ['motor', 'buildings', 'contents'];
  function C(v) { return 'var(--s-' + v + ')'; }
  function f(v, dec, lang) { return G.fmt(v, { dec: dec }, lang); }

  var figuras = {
    flujo: function (cont, lang, o) { cont.innerHTML = D.flujo(lang, { filas: o && o.filas }); },
    validacion_diseno: function (cont, lang) { cont.innerHTML = D.validacion(lang); },
    flujo_ia: function (cont, lang) { cont.innerHTML = D.ia(lang); },
    siniestros: function (cont, lang) { cont.innerHTML = D.siniestros(lang); },

    curva: function (cont, lang, o) {
      var e = CIFRAS.envios, l = L[lang], en = lang === 'en';
      var etiquetas = e.map(function (_, i) { return String(i + 1); });
      var det = e.map(function (x, i) { return (i + 1) + '. ' + (en ? x.etiqueta_en : x.etiqueta_es); });
      var ult = e.length - 1, iMod = -1, iS0 = -1, iS1 = -1, iF0 = -1, iF1 = -1, iFin = ult;
      e.forEach(function (x, i) {
        if (x.tipo === 'modelo') iMod = i;
        if (x.tipo === 'sonda') { if (iS0 < 0) iS0 = i; iS1 = i; }
        if (x.tipo === 'sonda_forma') { if (iF0 < 0) iF0 = i; iF1 = i; }
        if (x.seleccion_final) iFin = i;
      });
      function serie(tipo, campo) { return e.map(function (x, i) { return { i: i, y: x.tipo === tipo ? x[campo] : null, destacar: i === iFin }; }); }
      var bandas = [{ desde: 8, hasta: 11, texto: '', margen: 11 }, { desde: iS0, hasta: iS1, texto: '', margen: 9 }];
      if (iF0 >= 0) bandas.push({ desde: iF0, hasta: iF1, texto: '', margen: 9 });
      return G.lineas(cont, Object.assign({
        ancho: 700, alto: 270, lang: lang, interactivo: !!(o && o.interactivo), margen: { t: 40, r: 104, b: 44, l: 50 },
        aria: en ? 'Public score and local 2024 validation for the ' + e.length + ' scored submissions, with the level and shape probes and the three calibrated candidates'
          : 'Puntuación pública y validación local de 2024 de los ' + e.length + ' envíos puntuados, con las sondas de nivel y de forma y los tres candidatos calibrados',
        x: { etiquetas: etiquetas, detalle: det, titulo: en ? 'Scored submissions, in order (17–22 Oct)' : 'Envíos puntuados, en orden (del 17 al 22 de octubre)' },
        y: { dominio: [0.06, 0.145], valores: [0.06, 0.08, 0.10, 0.12, 0.14], formato: function (v) { return f(v, 2, lang); }, titulo: 'D² Tweedie (p = 1,5)'.replace(',', en ? '.' : ',') },
        bandas: bandas,
        series: [
          { id: 'local', nombre: l.local, color: 'var(--acento-2)', puntos: serie('modelo', 'v24_local'), radio: 3.5 },
          { id: 'pub', nombre: l.publico, color: 'var(--acento)', puntos: serie('modelo', 'publico'), radio: 3.5 },
          { id: 'sonda', nombre: en ? 'Probe' : 'Sonda', color: 'var(--s-gris)', grosor: 0.001, radio: 3.5,
            tipoLeyenda: 'punto', huecoLeyenda: true, puntos: e.map(function (x, i) { return { i: i, y: (x.tipo === 'sonda' || x.tipo === 'sonda_forma') ? x.publico : null, hueco: true }; }) },
          { id: 'cal', nombre: en ? 'Calibrated file' : 'Archivo calibrado', color: 'var(--acento)', grosor: 0.001, tipoLeyenda: 'punto',
            puntos: serie('calibracion', 'publico') }
        ],
        notas: [
          { i: 1.15, y: 0.0665, dx: 0, dy: 0, texto: en ? '← constant rate per line' : '← tasa constante por ramo', ancla: 'start' },
          { i: 9.5, y: 0.1005, dx: 0, dy: 0, texto: en ? 'better local score,\nworse public score' : 'mejor puntuación local,\npeor puntuación pública', ancla: 'middle' },
          { i: (iS0 + iS1) / 2, y: 0.1005, dx: 0, dy: 0, texto: en ? 'level\nprobes' : 'sondas\nde nivel', ancla: 'middle' },
          { i: (iF0 + iF1) / 2, y: 0.1005, dx: 0, dy: 0, texto: en ? 'shape\nprobes' : 'sondas\nde forma', ancla: 'middle' },
          { i: iMod, y: e[iMod].v24_local, dx: 0, dy: -10, ancla: 'middle', texto: f(e[iMod].v24_local, 5, lang) },
          { i: iFin, y: e[iFin].publico, dx: 10, dy: iFin === ult ? 4 : -12, ancla: 'start', fuerte: true, texto: 'Final: ' + f(e[iFin].publico, 5, lang) }
        ]
      }, (o && o.cfg) || {}));
    },

    calibracion: function (cont, lang, o) {
      // Sondas por ramo frente al marcador público. Fila de nivel: puntuación según el factor sobre el nivel 2025 de un ramo
      // (forma cerrada por las dos sondas y el modelo). Fila de forma: puntuación según el exponente que comprime o amplía
      // las diferencias de tasa del ramo (parábola por las dos sondas y S42). En las dos, el óptimo del público queda hueco y
      // la entrega final recorre solo la parte creíble del camino.
      var cal = CIFRAS.calibracion_nivel, fo = CIFRAS.calibracion_forma, ef = CIFRAS.entrega_final, en = lang === 'en', l = L[lang];
      var final = ef.codigo;
      // S43 lleva nivel y forma; S41 y S42 solo calibran el nivel, así que la figura queda en una fila.
      var filas = (o && o.filas) || (final === 'S43' ? ['nivel', 'forma'] : ['nivel']);
      var solo = filas.length === 1;
      var A = (o && o.ancho) || 700, H = (o && o.alto) || (filas.length > 1 ? 420 : 238), gap = 14, wP = (A - 2 * gap) / 3;
      var hLey = solo ? 0 : 24, hFila = (H - hLey) / filas.length;
      cont.textContent = '';
      var svg = G.el('svg', { viewBox: '0 0 ' + A + ' ' + H, width: A, height: H, role: 'img', class: 'g-svg',
        'aria-label': solo ? (en ? 'Public score as a function of the factor applied to one line\'s 2025 level: two probes and the model trace the curve; its peak is the public optimum and the final submission moves only part of the way'
          : 'Puntuación pública según el factor aplicado al nivel 2025 de un ramo: dos sondas y el modelo trazan la curva; su máximo es el óptimo del público y la entrega final recorre solo parte del camino')
          : (en ? 'Public score against the 2025 level factor (top) and the shape exponent (bottom) of each line: the probes and the model trace each curve; its peak is the public optimum and the final submission moves only part of the way'
          : 'Puntuación pública según el factor de nivel 2025 (arriba) y el exponente de forma (abajo) de cada ramo: las sondas y el modelo trazan cada curva; su máximo es el óptimo del público y la entrega final recorre solo parte del camino') }, cont);
      function fx(v) { return v.toFixed(2).replace('.', en ? '.' : ','); }
      function fila(tipo, y0) {
        var nivel = tipo === 'nivel';
        var m = { l: 42, r: 46, t: 40, b: solo ? 40 : 30 }, dom = nivel ? (solo ? [0.1284, 0.1304] : [0.1284, 0.1306]) : [0.1293, 0.1309], cx0 = nivel ? 0.88 : 0.86, cx1 = nivel ? 1.12 : 1.14;
        RAMOS.forEach(function (r, k) {
          var x0 = k * (wP + gap), z = nivel ? cal.ramos[r] : fo.ramos[r];
          var X = function (c) { return x0 + m.l + (c - cx0) / (cx1 - cx0) * (wP - m.l - m.r); };
          var Y = function (v) { return y0 + m.t + (dom[1] - v) / (dom[1] - dom[0]) * (hFila - m.t - m.b); };
          var d2 = nivel ? function (c) { return cal.publico_modelo - 4 * (z.S1_sobre_N * (Math.pow(c, -0.5) - 1) + z.S2_sobre_N * (Math.pow(c, 0.5) - 1)); }
            : function (a) { return fo.publico_S42 + z.alfa * (a - 1) + z.beta * (a - 1) * (a - 1); };
          var opt = nivel ? z.c_optimo : z.a_optimo, apl = nivel ? z.c_S42 : z.a_Z;
          var etiq = final;
          if (nivel && final === 'S41') apl = z.c_S41;
          G.texto(svg, x0 + m.l, y0 + (solo ? 14 : 12), l[r] + (solo ? '' : nivel ? (en ? ' · level' : ' · nivel') : (en ? ' · shape' : ' · forma')), { class: 'g-cat g-fuerte' });
          G.texto(svg, x0 + m.l, y0 + (solo ? 29 : 26), (en ? 'optimum ' : 'óptimo ') + (nivel ? '×' : 'a = ') + G.fmt(opt, { dec: 3 }, lang) + ' · ' + etiq + (nivel ? ' ×' : ' a = ') + G.fmt(apl, { dec: 3 }, lang), { class: 'g-nota' });
          var ticksY = nivel ? [0.129, 0.1295, 0.130] : [0.1295, 0.130, 0.1305];
          ticksY.forEach(function (v) {
            G.el('line', { x1: x0 + m.l, x2: x0 + wP - m.r, y1: Y(v), y2: Y(v), style: 'stroke: var(--grid); stroke-width: 1' }, svg);
            G.texto(svg, x0 + m.l - 5, Y(v) + 3.5, G.fmt(v, { dec: 4 }, lang), { 'text-anchor': 'end', class: 'g-tick' });
          });
          G.el('line', { x1: x0 + m.l, x2: x0 + wP - m.r, y1: y0 + hFila - m.b, y2: y0 + hFila - m.b, style: 'stroke: var(--axis); stroke-width: 1' }, svg);
          [0.90, 1.00, 1.10].forEach(function (c) {
            G.el('line', { x1: X(c), x2: X(c), y1: y0 + hFila - m.b, y2: y0 + hFila - m.b + 4, style: 'stroke: var(--axis); stroke-width: 1' }, svg);
            G.texto(svg, X(c), y0 + hFila - m.b + (solo ? 15 : 14), (nivel ? '×' : 'a ') + fx(c), { 'text-anchor': 'middle', class: 'g-tick' });
          });
          var dpath = '', abierto = false;
          for (var q = 0; q <= 96; q++) {
            var c = cx0 + q * (cx1 - cx0) / 96, v = d2(c);
            if (v < dom[0] || v > dom[1]) { abierto = false; continue; }
            dpath += (abierto ? 'L' : 'M') + X(c).toFixed(1) + ' ' + Y(v).toFixed(1); abierto = true;
          }
          G.el('path', { d: dpath, style: 'fill: none; stroke:' + C(r) + '; stroke-width: 2' }, svg);
          if (!nivel) {
            // Óptimo de 2024 en términos relativos a S30 (sin marcador): triángulo gris sobre el eje.
            var a24 = z.a_optimo_2024_relativo_S30, ya = y0 + hFila - m.b;
            G.el('path', { d: 'M' + (X(a24) - 4.5).toFixed(1) + ' ' + (ya - 0.5) + 'L' + (X(a24) + 4.5).toFixed(1) + ' ' + (ya - 0.5) + 'L' + X(a24).toFixed(1) + ' ' + (ya - 8.5) + 'Z',
              style: 'fill: var(--text-muted); stroke: var(--surface-1); stroke-width: 1' }, svg);
          }
          var cerca = Math.abs(opt - apl) < 0.02, izq = apl < opt;
          G.el('line', { x1: X(apl), x2: X(apl), y1: Y(d2(apl)) + 6, y2: y0 + hFila - m.b, style: 'stroke: var(--acento); stroke-width: 1; stroke-dasharray: 3 3' }, svg);
          G.el('circle', { cx: X(opt), cy: Y(d2(opt)), r: 4.5, style: 'fill: var(--surface-1); stroke: var(--text-primary); stroke-width: 1.8' }, svg);
          G.el('circle', { cx: X(apl), cy: Y(d2(apl)), r: 4.5, style: 'fill: var(--acento); stroke: var(--surface-1); stroke-width: 1.5' }, svg);
          G.texto(svg, X(apl) + (cerca ? (izq ? -7 : 7) : 0), Y(d2(apl)) - 9, etiq, { 'text-anchor': cerca ? (izq ? 'end' : 'start') : 'middle', class: 'g-val g-fuerte' });
          var pts = nivel ? [[0.90, z.publico_x090], [1.00, cal.publico_modelo], [1.10, z.publico_x110]] : [[0.90, z.publico_a090], [1.00, fo.publico_S42], [1.10, z.publico_a110]];
          pts.forEach(function (p, j) {
            G.el('circle', { cx: X(p[0]), cy: Y(p[1]), r: 3.4, style: 'fill: var(--text-primary); stroke: var(--surface-1); stroke-width: 1.5' }, svg);
            if (j === 0) G.texto(svg, X(p[0]) + 5, Y(p[1]) + 14, G.fmt(p[1], { dec: 5 }, lang), { 'text-anchor': 'start', class: 'g-val' });
            if (j === 2) G.texto(svg, X(p[0]) + 6, Y(p[1]) + (Y(p[1]) < y0 + m.t + 30 ? 16 : 4), G.fmt(p[1], { dec: 5 }, lang), { 'text-anchor': 'start', class: 'g-val' });
          });
          // La entrega final se dibuja encima de los puntos medidos: en autos queda junto al modelo (×1,00) y no debe taparse.
          G.el('circle', { cx: X(apl), cy: Y(d2(apl)), r: 4.5, style: 'fill: var(--acento); stroke: var(--surface-1); stroke-width: 1.5' }, svg);
        });
      }
      filas.forEach(function (t, i) { fila(t, i * hFila); });
      var yl = H - 6;
      G.el('circle', { cx: 6, cy: yl - 4, r: 3.4, style: 'fill: var(--text-primary)' }, svg);
      if (solo) {
        // Una fila: la leyenda del análisis de nivel tal como se presentó con S42, con el factor de la entrega final.
        G.texto(svg, 14, yl, en ? 'Public score returned by Kaggle (probes ×0.90 and ×1.10; the model at ×1.00)' : 'Puntuación pública devuelta por Kaggle (sondas ×0,90 y ×1,10; el modelo en ×1,00)', { class: 'g-ley' });
        var xs = en ? 448 : 456;
        G.el('circle', { cx: xs, cy: yl - 4, r: 4, style: 'fill: var(--surface-1); stroke: var(--text-primary); stroke-width: 1.8' }, svg);
        G.texto(svg, xs + 8, yl, en ? 'public optimum' : 'óptimo del público', { class: 'g-ley' });
        G.el('circle', { cx: xs + 112, cy: yl - 4, r: 4, style: 'fill: var(--acento)' }, svg);
        G.texto(svg, xs + 120, yl, en ? final + ' factor' : 'factor de ' + final, { class: 'g-ley' });
        return svg;
      }
      G.texto(svg, 14, yl, en ? "Kaggle's public score (probes and model)" : 'Puntuación pública de Kaggle (sondas y modelo)', { class: 'g-ley' });
      var xb = en ? 262 : 290;
      G.el('circle', { cx: xb, cy: yl - 4, r: 4, style: 'fill: var(--surface-1); stroke: var(--text-primary); stroke-width: 1.8' }, svg);
      G.texto(svg, xb + 8, yl, en ? 'public optimum' : 'óptimo del público', { class: 'g-ley' });
      G.el('circle', { cx: xb + (en ? 112 : 128), cy: yl - 4, r: 4, style: 'fill: var(--acento)' }, svg);
      G.texto(svg, xb + (en ? 120 : 136), yl, en ? 'final submission' : 'entrega final', { class: 'g-ley' });
      if (filas.indexOf('forma') >= 0) {
        var xt = xb + (en ? 232 : 232);
        G.el('path', { d: 'M' + (xt - 4.5) + ' ' + (yl - 0.5) + 'L' + (xt + 4.5) + ' ' + (yl - 0.5) + 'L' + xt + ' ' + (yl - 8.5) + 'Z', style: 'fill: var(--text-muted)' }, svg);
        G.texto(svg, xt + 8, yl, en ? '2024 shape optimum' : 'óptimo de forma de 2024', { class: 'g-ley' });
      }
      return svg;
    },

    publico_local: function (cont, lang, o) {
      var pv = CIFRAS.publico_vs_local, l = L[lang];
      var wrap = document.createElement('div'); wrap.className = 'g-par'; cont.textContent = ''; cont.appendChild(wrap);
      [['d2_completo_v24', l.comp, pv.spearman_completo, [0.1315, 0.1390]], ['d2_cuerpo_v24', l.cuerpo, pv.spearman_cuerpo_05, [0.0915, 0.0980]]].forEach(function (cfgp) {
        var d = document.createElement('div'); wrap.appendChild(d);
        var pts = pv.candidatos_antes.map(function (c) { return { x: c[cfgp[0]], y: c.publico, color: 'var(--s-gris)', etiqueta: '' }; });
        pv.posteriores.forEach(function (c) { pts.push({ x: c[cfgp[0]], y: c.publico, color: 'var(--acento)', etiqueta: c.cand === 'S30' ? l.s30 : '', fuerte: true, dx: -8, dy: -8, ancla: 'end' }); });
        G.dispersion(d, {
          ancho: 340, alto: 230, lang: lang, interactivo: !!(o && o.interactivo),
          x: { dominio: cfgp[3], ticks: 3, formato: function (v) { return f(v, 3, lang); }, titulo: (lang === 'en' ? 'Local D² 2024, ' : 'D² local 2024, ') + cfgp[1], corto: 'local' },
          y: { dominio: [0.1235, 0.1305], ticks: 3, formato: function (v) { return f(v, 3, lang); }, titulo: lang === 'en' ? 'Public score' : 'Puntuación pública', corto: lang === 'en' ? 'public' : 'pública' },
          puntos: pts, margen: { t: 30, r: 14, b: 40, l: 50 },
          nota: (lang === 'en' ? 'Rank correlation ' : 'Correlación de rangos ') + f(cfgp[2], 2, lang)
        });
      });
    },

    completitud: function (cont, lang, o) {
      var c = CIFRAS.ibnr.completitud_2024_por_peligro.slice();
      var orden = { motor: 0, buildings: 1, contents: 2 };
      c.sort(function (a, b) { return orden[a.ramo] - orden[b.ramo] || a.completitud_2024 - b.completitud_2024; });
      var cats = c.map(function (x) { return { id: x.ramo + ':' + x.peligro, etiqueta: PELIGROS[lang][x.peligro] + ' (' + L[lang][x.ramo].toLowerCase() + ')', fuerte: x.completitud_2024 < 0.8 }; });
      var vals = {}, colores = {};
      c.forEach(function (x) { vals[x.ramo + ':' + x.peligro] = x.completitud_2024; colores[x.ramo + ':' + x.peligro] = C(x.ramo); });
      return G.barras(cont, Object.assign({
        ancho: 380, alto: 330, lang: lang, orientacion: 'h', categorias: cats, series: [{ id: 'c', nombre: 'completitud' }],
        valores: { c: vals }, colorPorCategoria: colores, dominio: [0, 1], leyenda: false, grosor: 12, interactivo: !!(o && o.interactivo), ticks: 2,
        formato: function (v) { return G.fmt(v, { pct: true }, lang); }, margen: { t: 8, r: 40, b: 22, l: 178 },
        formatoEtiqueta: function (v) { return G.fmt(v, { pct: true, dec: 0 }, lang); },
        aria: lang === 'en' ? 'Share of 2024 exposure already reported by peril' : 'Parte de la exposición de 2024 ya reportada, por peligro'
      }, (o && o.cfg) || {}));
    },

    prima_anual: function (cont, lang, o) {
      var p = CIFRAS.ibnr.prima_riesgo_por_anio, l = L[lang];
      var wrap = document.createElement('div'); wrap.className = 'g-tres'; cont.textContent = ''; cont.appendChild(wrap);
      var dominios = { motor: [400, 650], buildings: [350, 530], contents: [95, 135] };
      RAMOS.forEach(function (r) {
        var d = document.createElement('div'); wrap.appendChild(d);
        var filas = p.filter(function (x) { return x.ramo === r; });
        var hist = filas.filter(function (x) { return x.anio <= 2024; });
        var pr = filas.filter(function (x) { return x.anio === 2025; })[0];
        var i25 = 4;
        G.lineas(d, {
          ancho: (o && o.ancho) || 236, alto: (o && o.alto) || 205, lang: lang, interactivo: !!(o && o.interactivo), margen: { t: 38, r: 16, b: 26, l: 40 },
          aria: l[r], leyenda: false,
          x: { etiquetas: ['2021', '2022', '2023', '2024', '2025'] },
          y: { dominio: dominios[r], ticks: 4, formato: function (v) { return f(v, 0, lang); } },
          series: [
            { id: 't0', nombre: l.t0, color: 'var(--s-gris)', puntos: hist.map(function (x, i) { return { i: i, y: x.prima_T0 }; }), radio: 3 },
            { id: 'ult', nombre: l.t0ibnr, color: C(r), puntos: hist.map(function (x, i) { return { i: i, y: x.prima_T0_mas_IBNR }; }).concat([{ i: i25, y: pr.prediccion_final, hueco: true }]) }
          ],
          notas: [
            { i: 3, y: hist[3].prima_T0, dx: 0, dy: 16, texto: f(hist[3].prima_T0, 0, lang) },
            { i: 3, y: hist[3].prima_T0_mas_IBNR, dx: 0, dy: -10, texto: f(hist[3].prima_T0_mas_IBNR, 0, lang) },
            { i: i25, y: pr.prediccion_final, dx: -2, dy: -11, ancla: 'end', fuerte: true, texto: f(pr.prediccion_final, 0, lang) }
          ]
        });
        var svgEl = d.querySelector('svg');
        G.texto(svgEl, 40, 14, l[r], { class: 'g-cat g-fuerte' });
      });
    },

    composicion: function (cont, lang, o) {
      var comp = CIFRAS.s30.composicion, l = L[lang];
      var series = [], vals = {}, segs = {};
      // Una serie por componente para apilar; color por tipo de modelo.
      comp.forEach(function (x, k) {
        var sid = 's' + k;
        series.push({ id: sid, nombre: COMP[lang][x.componente] + ' (' + L[lang][x.ramo] + ')', color: x.tipo === 'coste_total' ? 'var(--acento-2)' : 'var(--acento)' });
        vals[sid] = {}; vals[sid][x.ramo] = x.peso;
        segs[sid] = {}; segs[sid][x.ramo] = COMP[lang][x.componente].split(' ')[0] + ' ' + G.fmt(x.peso, { dec: 1 }, lang);
      });
      var svg = G.barras(cont, Object.assign({
        ancho: 700, alto: 150, lang: lang, orientacion: 'h', modo: 'apilado', categorias: RAMOS.map(function (r) { return { id: r, etiqueta: l[r] }; }),
        series: series, valores: vals, etiquetasSegmento: segs, dominio: [0, 1], leyenda: false, etiquetas: false, grosor: 26, interactivo: !!(o && o.interactivo),
        formato: function (v) { return G.fmt(v, { pct: true }, lang); }, margen: { t: 30, r: 26, b: 22, l: 84 },
        aria: lang === 'en' ? 'Final model weights by line and component type' : 'Pesos del modelo final por ramo y tipo de componente'
      }, (o && o.cfg) || {}));
      var g = G.el('g', {}, svg);
      G.el('rect', { x: 84, y: 6, width: 11, height: 11, rx: 2, style: 'fill: var(--acento)' }, g);
      G.texto(g, 100, 15, l.fs, { class: 'g-ley' });
      G.el('rect', { x: 260, y: 6, width: 11, height: 11, rx: 2, style: 'fill: var(--acento-2)' }, g);
      G.texto(g, 276, 15, l.ft, { class: 'g-ley' });
      return svg;
    },

    d2_ramo: function (cont, lang, o) {
      var v = CIFRAS.validacion, l = L[lang], corte = (o && o.corte) || 'V24';
      var cats = ['motor', 'buildings', 'contents', 'agregado'].map(function (k) { return { id: k, etiqueta: l[k], fuerte: k === 'agregado' }; });
      var ref = v.referencia_m00[corte], s30 = v.d2_recalculado[corte];
      return G.barras(cont, Object.assign({
        ancho: 380, alto: 220, lang: lang, orientacion: 'h', categorias: cats,
        series: [{ id: 'ref', nombre: l.ref, color: 'var(--s-gris)' }, { id: 's30', nombre: l.s30, color: 'var(--acento)' }],
        valores: { ref: ref, s30: s30 }, dominio: [0, 0.16], grosor: 12, interactivo: !!(o && o.interactivo), ticks: 4,
        formato: function (x) { return f(x, 2, lang); }, formatoEtiqueta: function (x) { return f(x, 3, lang); }, margen: { t: 34, r: 40, b: 22, l: 84 },
        aria: lang === 'en' ? 'D² by line in ' + corte : 'D² por ramo en ' + corte
      }, (o && o.cfg) || {}));
    },

    deciles: function (cont, lang, o) {
      var dz = CIFRAS.validacion.deciles_v24, l = L[lang];
      var wrap = document.createElement('div'); wrap.className = 'g-tres'; cont.textContent = ''; cont.appendChild(wrap);
      RAMOS.forEach(function (r) {
        var d = document.createElement('div'); wrap.appendChild(d);
        var filas = dz[r];
        G.lineas(d, {
          ancho: (o && o.ancho) || 236, alto: (o && o.alto) || 205, lang: lang, interactivo: !!(o && o.interactivo), margen: { t: 38, r: 12, b: 34, l: 44 }, leyenda: false,
          aria: l[r],
          x: { etiquetas: filas.map(function (x) { return String(x.decil); }), titulo: l.decil },
          y: { dominio: [8, 2000], log: true, valoresLog: [10, 30, 100, 300, 1000], formato: function (v) { return G.fmt(v, {}, lang); } },
          series: [
            { id: 'pred', nombre: l.pred, color: C(r), puntos: filas.map(function (x, i) { return { i: i, y: x.predicha }; }), marcadores: false },
            { id: 'obs', nombre: l.obs, color: 'var(--text-primary)', grosor: 0.001, puntos: filas.map(function (x, i) { return { i: i, y: x.observada, hueco: true }; }), radio: 3.2 }
          ]
        });
        if (r === 'motor' && !(o && o.sinLeyenda)) {
          var sv = d.querySelector('svg'), gl = G.el('g', {}, sv);
          var ya = ((o && o.alto) || 205) - 66;
          G.el('line', { x1: 140, x2: 154, y1: ya, y2: ya, style: 'stroke: var(--s-motor); stroke-width: 2.5; stroke-linecap: round' }, gl);
          G.texto(gl, 158, ya + 3.5, l.pred, { class: 'g-ley' });
          G.el('circle', { cx: 147, cy: ya + 15, r: 3.2, style: 'fill: var(--surface-1); stroke: var(--text-primary); stroke-width: 2' }, gl);
          G.texto(gl, 158, ya + 18.5, l.obs, { class: 'g-ley' });
        }
        var svgEl = d.querySelector('svg');
        G.texto(svgEl, 44, 14, l[r], { class: 'g-cat g-fuerte' });
        var top = CIFRAS.validacion.concentracion_v24[r].decil_superior_observado;
        G.texto(svgEl, 44, 28, (lang === 'en' ? 'top 10% holds ' : 'el 10 % más caro reúne ') + G.fmt(top, { pct: true, dec: 0 }, lang), { class: 'g-nota' });
      });
    },

    reservas: function (cont, lang, o) {
      var rs = CIFRAS.validacion.reservas.V24, l = L[lang];
      var cats = ['motor', 'buildings', 'contents', 'agregado'].map(function (k) { return { id: k, etiqueta: l[k] }; });
      var vals = { a: {}, b: {}, c: {} };
      cats.forEach(function (c) { vals.a[c.id] = rs['0.75'][c.id]; vals.b[c.id] = rs['1.0'][c.id]; vals.c[c.id] = rs['1.25'][c.id]; });
      return G.barras(cont, Object.assign({
        ancho: 420, alto: 290, lang: lang, orientacion: 'h', categorias: cats,
        series: [{ id: 'a', nombre: l.res[0], color: 'var(--ord-1)' }, { id: 'b', nombre: l.res[1], color: 'var(--ord-2)' }, { id: 'c', nombre: l.res[2], color: 'var(--ord-3)' }],
        valores: vals, dominio: [0, 0.16], grosor: 10, interactivo: !!(o && o.interactivo),
        formato: function (x) { return f(x, 2, lang); }, formatoEtiqueta: function (x) { return f(x, 3, lang); }, margen: { t: 46, r: 40, b: 22, l: 84 },
        aria: lang === 'en' ? 'D² 2024 under three case-reserve scenarios' : 'D² de 2024 con tres escenarios de reserva de caso'
      }, (o && o.cfg) || {}));
    },

    ceros: function (cont, lang, o) {
      // 100 periodos por ramo; se colorean los que tuvieron coste en 2024.
      var p = CIFRAS.datos.periodos_sin_coste_pct, l = L[lang], en = lang === 'en';
      var A = (o && o.ancho) || 600, hueco = 24, lado = Math.min(177, (A - 8 - 2 * hueco) / 3), sep = lado > 150 ? 3 : 2.5;
      var celda = (lado - 9 * sep) / 10, paso = celda + sep, H = 50 + lado + 30;
      cont.textContent = '';
      var svg = G.el('svg', { viewBox: '0 0 ' + A + ' ' + H, width: A, height: H, role: 'img', class: 'g-svg',
        'aria-label': en ? 'Out of every 100 policy periods of 2024, how many had a claim cost, by line' : 'De cada 100 periodos de póliza de 2024, cuántos tuvieron coste, por ramo' }, cont);
      RAMOS.forEach(function (r, k) {
        var x0 = 4 + k * (lado + hueco), y0 = 50, con = 100 - p[r]['2024'], nCon = Math.round(con);
        G.texto(svg, x0, 15, l[r], { class: 'g-cat g-fuerte' });
        G.texto(svg, x0, 34, G.fmt(con / 100, { pct: true, dec: 1 }, lang) + (en ? ' with a claim cost' : ' con coste'), { class: 'g-nota' });
        for (var i = 0; i < 100; i++) {
          var fila = Math.floor(i / 10), col = i % 10;
          G.el('rect', { x: x0 + col * paso, y: y0 + fila * paso, width: celda, height: celda, rx: 2.5,
            style: 'fill:' + (i < nCon ? C(r) : 'var(--grid)') }, svg);
        }
      });
      G.texto(svg, 4, H - 4, en ? 'Each square is one policy period in 2024; coloured squares had a claim cost.' : 'Cada cuadro es un periodo de póliza de 2024; los coloreados tuvieron coste.', { class: 'g-nota' });
      return svg;
    },

    escala_d2: function (cont, lang, o) {
      // Dónde caen las referencias en la escala del D² Tweedie.
      var v = CIFRAS.validacion, en = lang === 'en';
      var ref = v.referencia_m00.V24.agregado, mod = v.d2_recalculado.V24.agregado, pub = CIFRAS.entrega_final.publico;
      var A = (o && o.ancho) || 600, H = 262, x0 = 14, x1 = A - 14, d1 = 0.16, yT = 150;
      function x(t) { return x0 + t / d1 * (x1 - x0); }
      cont.textContent = '';
      var svg = G.el('svg', { viewBox: '0 0 ' + A + ' ' + H, width: A, height: H, role: 'img', class: 'g-svg',
        'aria-label': en ? 'Tweedie D² scale with the constant rate per line, the final model on 2024 and the public score' : 'Escala del D² Tweedie con la tasa constante por ramo, el modelo final en 2024 y la puntuación pública' }, cont);
      G.texto(svg, x0, 18, 'D² = 1 − ' + (en ? 'deviance of the model / deviance of the average' : 'desviación del modelo / desviación del promedio'), { class: 'g-cat g-fuerte' });
      G.texto(svg, x0, 38, en ? 'Tweedie deviance with power 1.5, summed over all periods' : 'Desviación Tweedie con potencia 1,5, sumada sobre todos los periodos', { class: 'g-nota' });
      G.el('line', { x1: x0, x2: x1, y1: yT, y2: yT, style: 'stroke: var(--axis); stroke-width: 2' }, svg);
      [0, 0.04, 0.08, 0.12, 0.16].forEach(function (t) {
        G.el('line', { x1: x(t), x2: x(t), y1: yT - 5, y2: yT + 5, style: 'stroke: var(--axis); stroke-width: 1.5' }, svg);
        G.texto(svg, x(t), yT + 22, G.fmt(t, { dec: 2 }, lang), { 'text-anchor': 'middle', class: 'g-tick' });
      });
      G.el('rect', { x: x(ref), y: yT - 7, width: x(mod) - x(ref), height: 14, rx: 3, style: 'fill: var(--banda)' }, svg);
      function marca(t, color, hueco, arriba, l1, l2, ancla) {
        var cx = x(t), yy = arriba ? yT - 46 : yT + 52;
        G.el('line', { x1: cx, x2: cx, y1: arriba ? yT - 34 : yT + 9, y2: arriba ? yT - 9 : yT + 36, style: 'stroke: var(--text-muted); stroke-width: 1' }, svg);
        G.el('circle', { cx: cx, cy: yT, r: 7, style: hueco ? 'fill: var(--surface-1); stroke:' + color + '; stroke-width: 2.5' : 'fill:' + color + '; stroke: var(--surface-1); stroke-width: 2' }, svg);
        G.texto(svg, cx, yy - (arriba ? 15 : 0), l1, { 'text-anchor': ancla || 'middle', class: 'g-val g-fuerte' });
        G.texto(svg, cx, yy + (arriba ? 0 : 15), l2, { 'text-anchor': ancla || 'middle', class: 'g-nota' });
      }
      G.texto(svg, x(0), yT - 22, en ? 'everyone pays' : 'todos pagan', { 'text-anchor': 'start', class: 'g-nota' });
      G.texto(svg, x(0), yT - 8, en ? 'the average' : 'el promedio', { 'text-anchor': 'start', class: 'g-nota' });
      marca(ref, 'var(--s-gris)', false, false, G.fmt(ref, { dec: 3 }, lang), en ? 'constant rate per line' : 'tasa constante por ramo', 'end');
      marca(mod, 'var(--acento)', false, true, G.fmt(mod, { dec: 3 }, lang), en ? 'final model, 2024 out of sample' : 'modelo final, 2024 fuera de muestra', 'end');
      marca(pub, 'var(--acento)', true, false, G.fmt(pub, { dec: 5 }, lang), en ? 'public score of the final submission' : 'puntuación pública de la entrega final', 'end');
      G.texto(svg, x0, H - 4, en ? 'The scale reaches 1 only if every period\'s cost were predicted exactly.' : 'La escala llega a 1 solo si se acertara el coste exacto de cada periodo.', { class: 'g-nota' });
      return svg;
    },

    hallazgos: function (cont, lang, o) {
      // Hallazgos del enjambre por área y estado (abiertos frente a atendidos).
      var lista = CIFRAS.validacion_ia.lista, en = lang === 'en';
      var areas = [['datos', en ? 'Data' : 'Datos'], ['modelos', en ? 'Models' : 'Modelos'], ['gobernanza', en ? 'Governance' : 'Gobierno']];
      var vals = { ab: {}, li: {}, at: {} }, segs = { ab: {}, li: {}, at: {} };
      areas.forEach(function (a) {
        var lim = function (h) { return h.estado.indexOf('limitacion_aceptada') === 0; };
        var ab = lista.filter(function (h) { return h.area === a[0] && h.estado === 'abierto'; }).length;
        var li = lista.filter(function (h) { return h.area === a[0] && lim(h); }).length;
        var at = lista.filter(function (h) { return h.area === a[0] && h.estado !== 'abierto' && !lim(h); }).length;
        vals.ab[a[0]] = ab; vals.li[a[0]] = li; vals.at[a[0]] = at;
        segs.ab[a[0]] = String(ab); segs.li[a[0]] = li ? String(li) : ''; segs.at[a[0]] = String(at);
      });
      return G.barras(cont, Object.assign({
        ancho: 420, alto: 190, lang: lang, orientacion: 'h', modo: 'apilado',
        categorias: areas.map(function (a) { return { id: a[0], etiqueta: a[1] }; }),
        series: [{ id: 'ab', nombre: en ? 'Open, with closure criterion' : 'Abiertos, con criterio de cierre', color: 'var(--st-warning)', colorTexto: '#0b0b0b' },
          { id: 'li', nombre: en ? 'Accepted as a declared limitation' : 'Aceptados como limitación declarada', color: 'var(--s-gris)' },
          { id: 'at', nombre: en ? 'Closed or remediated' : 'Cerrados o remediados', color: 'var(--st-good)' }],
        valores: vals, etiquetasSegmento: segs, dominio: [0, 8], etiquetas: false, grosor: 26, ticks: 4,
        interactivo: !!(o && o.interactivo), formato: function (v) { return G.fmt(v, {}, lang); }, margen: { t: 60, r: 16, b: 24, l: 92 },
        aria: en ? 'Validation swarm findings by area and state' : 'Hallazgos del enjambre de validación por área y estado'
      }, (o && o.cfg) || {}));
    },

    backtest: function (cont, lang, o) {
      // Backtesting del IBNR: lo que el chain-ladder proyectaba reportar después de cada corte, frente a lo reportado hasta 12-2024.
      var bt = CIFRAS.sensibilidad.backtest_ibnr, en = lang === 'en', l = L[lang];
      var nombres = en ? { '2022-12': 'Cut Dec 2022', '2023-12': 'Cut Dec 2023', '2024-06': 'Cut Jun 2024' }
        : { '2022-12': 'Corte dic. 2022', '2023-12': 'Corte dic. 2023', '2024-06': 'Corte jun. 2024' };
      var filas = bt.celdas.filter(function (x) { return x.corte === bt.cortes[0]; });
      function celda(c, x) { return bt.celdas.filter(function (q) { return q.corte === c && q.ramo === x.ramo && q.peligro === x.peligro; })[0]; }
      function pc(v) { var r = Math.round(v * 100); return (r > 0 ? '+' : r < 0 ? '−' : '') + G.fmt(Math.abs(r) / 100, { pct: true, dec: 0 }, lang); }
      var A = (o && o.ancho) || 640, xL = 4, wL = 196, wC = 66, x0 = xL + wL + wC, gap = 6, nC = bt.cortes.length;
      var wCel = (A - x0 - 4 - gap * (nC - 1)) / nC, hF = 20, yH = 36, sepR = 7;
      var H = yH + filas.length * hF + 2 * sepR + 44;
      cont.textContent = '';
      var svg = G.el('svg', { viewBox: '0 0 ' + A + ' ' + H, width: A, height: H, role: 'img', class: 'g-svg',
        'aria-label': en ? 'IBNR backtest: error of the claims projected after each cut against those reported by December 2024, by peril'
          : 'Backtesting del IBNR: error de los avisos proyectados tras cada corte frente a los reportados hasta diciembre de 2024, por peligro' }, cont);
      G.texto(svg, xL, 22, en ? 'Peril (line)' : 'Peligro (ramo)', { class: 'g-ley g-fuerte' });
      G.texto(svg, xL + wL + wC / 2, 22, en ? 'Criterion' : 'Criterio', { 'text-anchor': 'middle', class: 'g-ley g-fuerte' });
      bt.cortes.forEach(function (c, k) { G.texto(svg, x0 + k * (wCel + gap) + wCel / 2, 22, nombres[c], { 'text-anchor': 'middle', class: 'g-ley g-fuerte' }); });
      var y = yH, previo = null;
      filas.forEach(function (x) {
        if (previo && x.ramo !== previo) y += sepR;
        previo = x.ramo;
        G.texto(svg, xL, y + 14, PELIGROS[lang][x.peligro] + ' (' + l[x.ramo].toLowerCase() + ')', { class: 'g-cat' + (x.largo ? ' g-fuerte' : '') });
        G.texto(svg, xL + wL + wC / 2, y + 14, '±' + G.fmt(x.limite, { pct: true, dec: 0 }, lang), { 'text-anchor': 'middle', class: 'g-tick' });
        bt.cortes.forEach(function (c, k) {
          var z = celda(c, x), cx = x0 + k * (wCel + gap);
          G.el('rect', { x: cx, y: y + 1.5, width: wCel, height: hF - 3, rx: 3,
            style: z.cumple ? 'fill: var(--grid)' : 'fill: var(--st-warning); stroke: #0b0b0b; stroke-width: 1' }, svg);
          var t = G.texto(svg, cx + wCel / 2, y + 14, pc(z.error), { 'text-anchor': 'middle', class: 'g-val' + (z.cumple ? '' : ' g-fuerte') });
          if (!z.cumple) t.setAttribute('style', 'fill: #0b0b0b');
        });
        y += hF;
      });
      var yl = y + 18;
      G.el('rect', { x: xL, y: yl - 10, width: 14, height: 12, rx: 2.5, style: 'fill: var(--grid)' }, svg);
      G.texto(svg, xL + 20, yl, en ? 'Within its criterion' : 'Dentro de su criterio', { class: 'g-ley' });
      G.el('rect', { x: xL + 170, y: yl - 10, width: 14, height: 12, rx: 2.5, style: 'fill: var(--st-warning); stroke: #0b0b0b; stroke-width: 1' }, svg);
      G.texto(svg, xL + 190, yl, en ? 'Outside its criterion' : 'Fuera de su criterio', { class: 'g-ley' });
      G.texto(svg, xL, yl + 20, en ? 'Error = (projected − reported) / reported. Bold rows: long-tail perils, criterion ±20%.'
        : 'Error = (proyectado − reportado) / reportado. En negrita, los peligros de cola larga, con criterio ±20 %.', { class: 'g-nota' });
      return svg;
    },

    foro: function (cont, lang, o) {
      var fb = CIFRAS.foro.por_bloque_6h;
      var tipos = [['preinscripcion', lang === 'en' ? 'Pre-registered hypothesis' : 'Hipótesis preinscrita', 'var(--acento)'],
        ['adverso', lang === 'en' ? 'Adverse result or discard' : 'Resultado adverso o descarte', 'var(--acento-2)'],
        ['validacion', lang === 'en' ? 'Validation and governance' : 'Validación y gobierno', 'var(--s-contents)'],
        ['resultado_o_coordinacion', lang === 'en' ? 'Results and coordination' : 'Resultados y coordinación', 'var(--s-gris)']];
      var cats = fb.map(function (b) { var p = b.bloque_utc.split(' '); return { id: b.bloque_utc, etiqueta: p[0].slice(8, 10) + '/' + p[0].slice(5, 7) + '\n' + p[1] + ' UTC' }; });
      var vals = {};
      tipos.forEach(function (t) { vals[t[0]] = {}; fb.forEach(function (b) { vals[t[0]][b.bloque_utc] = b[t[0]] || 0; }); });
      return G.barras(cont, Object.assign({
        ancho: 520, alto: 250, lang: lang, orientacion: 'v', modo: 'apilado', categorias: cats,
        series: tipos.map(function (t) { return { id: t[0], nombre: t[1], color: t[2] }; }), valores: vals, grosor: 30,
        interactivo: !!(o && o.interactivo), formato: function (x) { return G.fmt(x, {}, lang); }, margen: { t: 50, r: 16, b: 46, l: 40 },
        aria: lang === 'en' ? 'Forum posts by six-hour block and type' : 'Aportes al foro por bloque de seis horas y tipo'
      }, (o && o.cfg) || {}));
    }
  };

  function dibujar(id, cont, lang, o) {
    if (!figuras[id]) throw new Error('figura desconocida: ' + id);
    return figuras[id](cont, lang || 'es', o || {});
  }
  global.F = { dibujar: dibujar, ids: Object.keys(figuras), L: L, PELIGROS: PELIGROS, COMP: COMP };
})(window);
