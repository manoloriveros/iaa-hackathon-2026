/* graficos.js: gráficos SVG sin dependencias para el informe, el panel y las láminas del video.
   Todo el texto se inserta con textContent. Los colores salen de variables CSS (ver estilo.css),
   así el mismo gráfico sirve en modo claro, oscuro e impreso. */
(function (global) {
  'use strict';
  var NS = 'http://www.w3.org/2000/svg';

  function el(tag, attrs, parent) {
    var n = document.createElementNS(NS, tag);
    if (attrs) {
      for (var k in attrs) {
        if (attrs[k] === undefined || attrs[k] === null) continue;
        if (k === 'style') n.setAttribute('style', attrs[k]);
        else n.setAttribute(k, attrs[k]);
      }
    }
    if (parent) parent.appendChild(n);
    return n;
  }

  function texto(parent, x, y, s, attrs) {
    var t = el('text', Object.assign({ x: x, y: y }, attrs || {}), parent);
    t.textContent = s;
    return t;
  }

  // Formato de números según idioma: es usa coma decimal y punto de miles; en, al revés.
  function fmt(v, opts, lang) {
    opts = opts || {};
    if (v === null || v === undefined || isNaN(v)) return '';
    var loc = (lang || 'es') === 'en' ? 'en-US' : 'es-ES';
    var o = { useGrouping: 'always' };
    if (opts.dec !== undefined) { o.minimumFractionDigits = opts.dec; o.maximumFractionDigits = opts.dec; }
    if (opts.pct) { o.style = 'percent'; }
    var s;
    if (opts.compacto && Math.abs(v) >= 1e6) {
      s = new Intl.NumberFormat(loc, Object.assign({}, o, { minimumFractionDigits: opts.decM === undefined ? 1 : opts.decM, maximumFractionDigits: opts.decM === undefined ? 1 : opts.decM })).format(v / 1e6) + ' M';
    } else if (opts.compacto && Math.abs(v) >= 1e3 && opts.k) {
      s = new Intl.NumberFormat(loc, Object.assign({}, o, { maximumFractionDigits: 1 })).format(v / 1e3) + ' k';
    } else {
      s = new Intl.NumberFormat(loc, o).format(v);
    }
    return (opts.prefijo || '') + s + (opts.sufijo || '');
  }

  function ticksBonitos(min, max, n) {
    var rango = max - min;
    if (rango <= 0) return [min];
    var paso0 = rango / Math.max(1, n);
    var mag = Math.pow(10, Math.floor(Math.log10(paso0)));
    var r = paso0 / mag;
    var paso = (r >= 5 ? 10 : r >= 2 ? 5 : r >= 1 ? 2 : 1) * mag;
    if (r < 1.5) paso = 1 * mag; else if (r < 3) paso = 2 * mag; else if (r < 7) paso = 5 * mag; else paso = 10 * mag;
    var t0 = Math.ceil(min / paso - 1e-9) * paso, out = [];
    for (var t = t0; t <= max + paso * 1e-9; t += paso) out.push(+t.toFixed(12));
    return out;
  }

  function escala(d0, d1, r0, r1, log) {
    if (log) {
      var l0 = Math.log10(d0), l1 = Math.log10(d1);
      return function (v) { return r0 + (Math.log10(v) - l0) / (l1 - l0) * (r1 - r0); };
    }
    return function (v) { return r0 + (v - d0) / (d1 - d0) * (r1 - r0); };
  }

  function svgBase(contenedor, ancho, alto, etiqueta) {
    contenedor.textContent = '';
    var svg = el('svg', { viewBox: '0 0 ' + ancho + ' ' + alto, width: ancho, height: alto, role: 'img', 'aria-label': etiqueta || '', class: 'g-svg' }, contenedor);
    return svg;
  }

  // Tooltip compartido: una sola caja flotante, valores en primer plano.
  var tip = null;
  function tooltip() {
    if (tip) return tip;
    tip = document.createElement('div');
    tip.className = 'g-tooltip';
    tip.setAttribute('role', 'status');
    document.body.appendChild(tip);
    return tip;
  }
  function mostrarTip(ev, filas, titulo) {
    var t = tooltip();
    t.textContent = '';
    if (titulo) { var h = document.createElement('div'); h.className = 'g-tip-t'; h.textContent = titulo; t.appendChild(h); }
    filas.forEach(function (f) {
      var row = document.createElement('div'); row.className = 'g-tip-f';
      if (f.color) { var k = document.createElement('span'); k.className = 'g-tip-k'; k.style.background = f.color; row.appendChild(k); }
      var v = document.createElement('strong'); v.textContent = f.valor; row.appendChild(v);
      var n = document.createElement('span'); n.className = 'g-tip-n'; n.textContent = f.nombre; row.appendChild(n);
      t.appendChild(row);
    });
    t.style.display = 'block';
    var x = ev.clientX + 14, y = ev.clientY + 14;
    var w = t.offsetWidth, h2 = t.offsetHeight;
    if (x + w > window.innerWidth - 8) x = ev.clientX - w - 14;
    if (y + h2 > window.innerHeight - 8) y = ev.clientY - h2 - 14;
    t.style.left = x + 'px'; t.style.top = y + 'px';
  }
  function ocultarTip() { if (tip) tip.style.display = 'none'; }

  function ejeY(svg, cfg, y, x0, x1, ticks, formato, lang) {
    var g = el('g', { class: 'g-eje' }, svg);
    ticks.forEach(function (t) {
      var yy = y(t);
      el('line', { x1: x0, x2: x1, y1: yy, y2: yy, style: 'stroke: var(--grid); stroke-width: 1' }, g);
      texto(g, x0 - 6, yy + 3.5, formato(t), { 'text-anchor': 'end', class: 'g-tick' });
    });
    if (cfg.y && cfg.y.titulo) {
      texto(g, x0, (cfg.margen ? cfg.margen.t : 20) - 10, cfg.y.titulo, { 'text-anchor': 'start', class: 'g-ytit' });
    }
  }

  function leyenda(svg, items, x, y, ancho) {
    // Mide cada elemento y lo coloca en filas dentro del ancho disponible.
    var g = el('g', { class: 'g-leyenda' }, svg), cx = x, cy = y, limite = x + (ancho || 9999);
    items.forEach(function (it) {
      var gi = el('g', {}, g);
      var t = texto(gi, 18, 0, it.nombre, { class: 'g-ley' });
      var w = 18 + (t.getComputedTextLength ? t.getComputedTextLength() : it.nombre.length * 6) + 18;
      if (cx > x && cx + w - 18 > limite) { cx = x; cy += 16; }
      if (it.tipo === 'linea') el('line', { x1: 0, x2: 14, y1: -3.5, y2: -3.5, style: 'stroke:' + it.color + '; stroke-width: 2.5; stroke-linecap: round' }, gi);
      else if (it.tipo === 'punto') el('circle', { cx: 6, cy: -3.5, r: 4, style: it.hueco ? 'fill: var(--surface-1); stroke:' + it.color + '; stroke-width: 2' : 'fill:' + it.color }, gi);
      else el('rect', { x: 0, y: -9, width: 11, height: 11, rx: 2, style: 'fill:' + it.color }, gi);
      gi.setAttribute('transform', 'translate(' + cx + ',' + cy + ')');
      cx += w;
    });
    return g;
  }

  /* Gráfico de líneas sobre un eje x categórico u ordenado.
     cfg: {ancho, alto, margen, lang, x:{etiquetas:[...], titulo}, y:{dominio:[a,b], ticks, formato, log, titulo},
           series:[{id, nombre, color, puntos:[{i, y, etiqueta, destacar}], marcadores, grosor, enfasis}],
           bandas:[{desde, hasta, texto}], notas:[{i, y, texto, dx, dy, ancla}], leyenda:true, aria} */
  function lineas(cont, cfg) {
    var A = cfg.ancho || 640, H = cfg.alto || 300, m = Object.assign({ t: 34, r: 24, b: 40, l: 54 }, cfg.margen || {});
    var lang = cfg.lang || 'es';
    var svg = svgBase(cont, A, H, cfg.aria);
    var n = cfg.x.etiquetas.length;
    var x = function (i) { return m.l + (n === 1 ? 0.5 : i / (n - 1)) * (A - m.l - m.r); };
    var dom = cfg.y.dominio;
    var y = escala(dom[0], dom[1], H - m.b, m.t, cfg.y.log);
    var ticks = cfg.y.valores || (cfg.y.log ? cfg.y.valoresLog : ticksBonitos(dom[0], dom[1], cfg.y.ticks || 5));
    var f = cfg.y.formato || function (v) { return fmt(v, { dec: 2 }, lang); };
    (cfg.bandas || []).forEach(function (b) {
      var xa = x(b.desde) - (b.margen || 10), xb = x(b.hasta) + (b.margen || 10);
      el('rect', { x: xa, y: m.t, width: xb - xa, height: H - m.b - m.t, style: 'fill: var(--banda)' }, svg);
      texto(svg, (xa + xb) / 2, m.t + 12, b.texto, { 'text-anchor': 'middle', class: 'g-banda' });
    });
    ejeY(svg, cfg, y, m.l, A - m.r, ticks, f, lang);
    el('line', { x1: m.l, x2: A - m.r, y1: H - m.b, y2: H - m.b, style: 'stroke: var(--axis); stroke-width: 1' }, svg);
    var cada = cfg.x.cada || 1;
    cfg.x.etiquetas.forEach(function (lab, i) {
      if (i % cada !== 0 && i !== n - 1) return;
      var t = texto(svg, x(i), H - m.b + 15, lab, { 'text-anchor': cfg.x.rotar ? 'end' : 'middle', class: 'g-tick' });
      if (cfg.x.rotar) t.setAttribute('transform', 'rotate(-35 ' + x(i) + ' ' + (H - m.b + 15) + ')');
    });
    if (cfg.x.titulo) texto(svg, (m.l + A - m.r) / 2, H - 6, cfg.x.titulo, { 'text-anchor': 'middle', class: 'g-xtit' });
    cfg.series.forEach(function (s) {
      var pts = s.puntos.filter(function (p) { return p.y !== null && p.y !== undefined; });
      var d = pts.map(function (p, k) { return (k ? 'L' : 'M') + x(p.i).toFixed(1) + ' ' + y(p.y).toFixed(1); }).join(' ');
      el('path', { d: d, style: 'fill: none; stroke:' + s.color + '; stroke-width:' + (s.grosor || 2) + '; stroke-linejoin: round; stroke-linecap: round' + (s.opacidad ? '; opacity:' + s.opacidad : '') }, svg);
      if (s.marcadores !== false) {
        pts.forEach(function (p) {
          var r = p.destacar ? 5.5 : (s.radio || 4);
          el('circle', { cx: x(p.i), cy: y(p.y), r: r + 2, style: 'fill: var(--surface-1)' }, svg);
          el('circle', { cx: x(p.i), cy: y(p.y), r: r, style: 'fill:' + (p.hueco ? 'var(--surface-1)' : (p.color || s.color)) + (p.hueco ? '; stroke:' + s.color + '; stroke-width: 2' : '') }, svg);
        });
      }
    });
    (cfg.notas || []).forEach(function (nt) {
      var px = x(nt.i), py = y(nt.y);
      var tx = px + (nt.dx || 0), ty = py + (nt.dy || -12);
      if (nt.guia) el('line', { x1: px, y1: py + (nt.dy > 0 ? 6 : -6), x2: tx, y2: ty + (nt.dy > 0 ? -10 : 3), style: 'stroke: var(--text-muted); stroke-width: 1' }, svg);
      var lineasNota = String(nt.texto).split('\n');
      lineasNota.forEach(function (ln, k) {
        texto(svg, tx, ty + k * 12, ln, { 'text-anchor': nt.ancla || 'middle', class: nt.fuerte ? 'g-nota g-fuerte' : 'g-nota' });
      });
    });
    if (cfg.leyenda !== false) {
      leyenda(svg, cfg.series.filter(function (s) { return !s.sinLeyenda; }).map(function (s) {
        return { tipo: s.tipoLeyenda || 'linea', color: s.color, nombre: s.nombre, hueco: s.huecoLeyenda };
      }), m.l, 14, A - m.l - m.r);
    }
    if (cfg.interactivo) {
      var cruz = el('line', { y1: m.t, y2: H - m.b, style: 'stroke: var(--text-muted); stroke-width: 1; display: none' }, svg);
      var zona = el('rect', { x: m.l - 10, y: m.t, width: A - m.l - m.r + 20, height: H - m.b - m.t, style: 'fill: transparent' }, svg);
      zona.addEventListener('pointermove', function (ev) {
        var pt = svg.createSVGPoint(); pt.x = ev.clientX; pt.y = ev.clientY;
        var loc = pt.matrixTransform(svg.getScreenCTM().inverse());
        var i = Math.max(0, Math.min(n - 1, Math.round((loc.x - m.l) / (A - m.l - m.r) * (n - 1))));
        cruz.setAttribute('x1', x(i)); cruz.setAttribute('x2', x(i)); cruz.style.display = 'block';
        var filas = cfg.series.map(function (s) {
          var p = s.puntos.filter(function (q) { return q.i === i; })[0];
          return p && p.y !== null && p.y !== undefined ? { color: s.color, valor: f(p.y), nombre: s.nombre } : null;
        }).filter(Boolean);
        var tituloTip = (cfg.x.detalle && cfg.x.detalle[i]) || cfg.x.etiquetas[i];
        mostrarTip(ev, filas, tituloTip);
      });
      zona.addEventListener('pointerleave', function () { cruz.style.display = 'none'; ocultarTip(); });
    }
    return svg;
  }

  /* Barras horizontales o verticales, agrupadas o apiladas.
     cfg: {ancho, alto, orientacion:'h'|'v', categorias:[{id, etiqueta}], series:[{id, nombre, color}],
           valores: {serieId: {catId: v}}, modo:'agrupado'|'apilado', dominio:[0,b], formato, etiquetas:true,
           etiquetasSegmento:{serieId:{catId:texto}}, grosor:max px, leyenda, log:{min,max,valores}} */
  function barras(cont, cfg) {
    var A = cfg.ancho || 640, H = cfg.alto || 300, lang = cfg.lang || 'es';
    var hor = (cfg.orientacion || 'h') === 'h';
    var m = Object.assign(hor ? { t: cfg.leyenda === false ? 10 : 30, r: 56, b: 24, l: 150 } : { t: 34, r: 16, b: 46, l: 50 }, cfg.margen || {});
    var svg = svgBase(cont, A, H, cfg.aria);
    var cats = cfg.categorias, ser = cfg.series, apilado = cfg.modo === 'apilado';
    var f = cfg.formato || function (v) { return fmt(v, { dec: 2 }, lang); };
    var maxV = cfg.dominio ? cfg.dominio[1] : Math.max.apply(null, cats.map(function (c) {
      if (apilado) return ser.reduce(function (a, s) { return a + ((cfg.valores[s.id] || {})[c.id] || 0); }, 0);
      return Math.max.apply(null, ser.map(function (s) { return (cfg.valores[s.id] || {})[c.id] || 0; }));
    })) * 1.08;
    var minV = cfg.dominio ? cfg.dominio[0] : 0;
    var log = !!cfg.log;
    var largo = hor ? A - m.l - m.r : H - m.t - m.b;
    var v2p = log ? escala(cfg.log.min, cfg.log.max, 0, largo, true) : escala(minV, maxV, 0, largo, false);
    var banda = (hor ? H - m.t - m.b : A - m.l - m.r) / cats.length;
    var grosorMax = cfg.grosor || 22, gap = 2;
    var nG = apilado ? 1 : ser.length;
    var grosor = Math.min(grosorMax, (banda * 0.72 - gap * (nG - 1)) / nG);
    var ticks = log ? cfg.log.valores : ticksBonitos(minV, maxV, cfg.ticks || 4);
    // rejilla
    ticks.forEach(function (t) {
      var p = v2p(t);
      if (hor) {
        el('line', { x1: m.l + p, x2: m.l + p, y1: m.t, y2: H - m.b, style: 'stroke: var(--grid); stroke-width: 1' }, svg);
        texto(svg, m.l + p, H - m.b + 14, f(t), { 'text-anchor': 'middle', class: 'g-tick' });
      } else {
        el('line', { x1: m.l, x2: A - m.r, y1: H - m.b - p, y2: H - m.b - p, style: 'stroke: var(--grid); stroke-width: 1' }, svg);
        texto(svg, m.l - 6, H - m.b - p + 3.5, f(t), { 'text-anchor': 'end', class: 'g-tick' });
      }
    });
    if (hor) el('line', { x1: m.l, x2: m.l, y1: m.t, y2: H - m.b, style: 'stroke: var(--axis); stroke-width: 1' }, svg);
    else el('line', { x1: m.l, x2: A - m.r, y1: H - m.b, y2: H - m.b, style: 'stroke: var(--axis); stroke-width: 1' }, svg);
    function rectRedondo(g, x0, y0, w, h, extremo, color, info) {
      // Extremo redondeado de 4 px solo en el lado del dato; base recta.
      var r = Math.min(4, (hor ? h : w) / 2, (hor ? w : h));
      var d;
      if (w <= 0 || h <= 0) return null;
      if (hor && extremo) d = 'M' + x0 + ' ' + y0 + 'H' + (x0 + w - r) + 'Q' + (x0 + w) + ' ' + y0 + ' ' + (x0 + w) + ' ' + (y0 + r) + 'V' + (y0 + h - r) + 'Q' + (x0 + w) + ' ' + (y0 + h) + ' ' + (x0 + w - r) + ' ' + (y0 + h) + 'H' + x0 + 'Z';
      else if (!hor && extremo) d = 'M' + x0 + ' ' + (y0 + h) + 'V' + (y0 + r) + 'Q' + x0 + ' ' + y0 + ' ' + (x0 + r) + ' ' + y0 + 'H' + (x0 + w - r) + 'Q' + (x0 + w) + ' ' + y0 + ' ' + (x0 + w) + ' ' + (y0 + r) + 'V' + (y0 + h) + 'Z';
      else d = 'M' + x0 + ' ' + y0 + 'h' + w + 'v' + h + 'h' + (-w) + 'Z';
      var p = el('path', { d: d, style: 'fill:' + color, class: 'g-barra', tabindex: cfg.interactivo ? 0 : null }, g);
      if (cfg.interactivo && info) {
        p.addEventListener('pointermove', function (ev) { mostrarTip(ev, [{ color: color, valor: info.valor, nombre: info.nombre }], info.cat); });
        p.addEventListener('pointerleave', ocultarTip);
        p.addEventListener('focus', function () { var b = p.getBoundingClientRect(); mostrarTip({ clientX: b.right, clientY: b.top }, [{ color: color, valor: info.valor, nombre: info.nombre }], info.cat); });
        p.addEventListener('blur', ocultarTip);
      }
      return p;
    }
    cats.forEach(function (c, ci) {
      var g = el('g', {}, svg);
      var centro = (hor ? m.t : m.l) + banda * (ci + 0.5);
      var lab = c.etiqueta;
      if (hor) {
        var lineasEt = String(lab).split('\n');
        lineasEt.forEach(function (ln, k) {
          texto(g, m.l - 8, centro + 4 - (lineasEt.length - 1) * 6 + k * 12, ln, { 'text-anchor': 'end', class: c.fuerte ? 'g-cat g-fuerte' : 'g-cat' });
        });
      } else {
        var lns = String(lab).split('\n');
        lns.forEach(function (ln, k) { texto(g, centro, H - m.b + 15 + k * 12, ln, { 'text-anchor': 'middle', class: 'g-cat' }); });
      }
      var acumulado = 0;
      ser.forEach(function (s, si) {
        var v = (cfg.valores[s.id] || {})[c.id];
        if (v === undefined || v === null) return;
        var color = (cfg.colorPorCategoria && cfg.colorPorCategoria[c.id]) || s.color;
        var largoV = log ? v2p(Math.max(v, cfg.log.min)) : v2p(v) - v2p(minV);
        var off = apilado ? (log ? 0 : v2p(acumulado) - v2p(minV)) : 0;
        var ultimo = !apilado || si === ser.length - 1 || ser.slice(si + 1).every(function (t) { return !((cfg.valores[t.id] || {})[c.id]); });
        var pos = apilado ? centro - grosor / 2 : centro - (nG * grosor + (nG - 1) * gap) / 2 + si * (grosor + gap);
        var x0, y0, w, h;
        var hueco = apilado && si > 0 ? gap : 0;
        if (hor) { x0 = m.l + off + hueco; y0 = pos; w = largoV - hueco; h = grosor; }
        else { w = grosor; h = largoV - hueco; x0 = pos; y0 = H - m.b - off - largoV; }
        rectRedondo(g, x0, y0, w, h, ultimo, color, { valor: f(v), nombre: s.nombre, cat: String(lab).replace(/\n/g, ' ') });
        var etSeg = cfg.etiquetasSegmento && cfg.etiquetasSegmento[s.id] && cfg.etiquetasSegmento[s.id][c.id];
        if (etSeg) {
          var tt = texto(g, x0 + w / 2, y0 + h / 2 + 3.5, etSeg, { 'text-anchor': 'middle', class: 'g-seg', style: s.colorTexto ? 'fill:' + s.colorTexto : null });
          var tw = tt.getComputedTextLength ? tt.getComputedTextLength() : etSeg.length * 6;
          if (tw > (hor ? w : h) - 8) tt.remove();
        }
        if (cfg.etiquetas !== false && (!apilado || ultimo)) {
          var tot = apilado ? acumulado + v : v;
          var et = cfg.formatoEtiqueta ? cfg.formatoEtiqueta(tot, c, s) : f(tot);
          if (hor) texto(g, x0 + w + 5, y0 + h / 2 + 3.5, et, { class: 'g-val' });
          else texto(g, x0 + w / 2, y0 - 5, et, { 'text-anchor': 'middle', class: 'g-val' });
        }
        acumulado += v;
      });
    });
    if (cfg.leyenda !== false && ser.length > 1) {
      leyenda(svg, ser.map(function (s) { return { tipo: 'rect', color: s.color, nombre: s.nombre }; }), hor ? m.l : m.l, 14, A - m.l - m.r);
    }
    if (cfg.notaFinal) texto(svg, A - m.r, H - 4, cfg.notaFinal, { 'text-anchor': 'end', class: 'g-nota' });
    return svg;
  }

  /* Dispersión con etiquetas por punto y área de acierto de 24 px.
     cfg: {ancho, alto, x:{dominio, formato, titulo}, y:{dominio, formato, titulo}, puntos:[{x, y, etiqueta, color, hueco, dx, dy}], nota} */
  function dispersion(cont, cfg) {
    var A = cfg.ancho || 360, H = cfg.alto || 260, lang = cfg.lang || 'es';
    var m = Object.assign({ t: 30, r: 16, b: 40, l: 52 }, cfg.margen || {});
    var svg = svgBase(cont, A, H, cfg.aria);
    var x = escala(cfg.x.dominio[0], cfg.x.dominio[1], m.l, A - m.r);
    var y = escala(cfg.y.dominio[0], cfg.y.dominio[1], H - m.b, m.t);
    var fx = cfg.x.formato || function (v) { return fmt(v, { dec: 3 }, lang); };
    var fy = cfg.y.formato || function (v) { return fmt(v, { dec: 3 }, lang); };
    ticksBonitos(cfg.y.dominio[0], cfg.y.dominio[1], cfg.y.ticks || 4).forEach(function (t) {
      el('line', { x1: m.l, x2: A - m.r, y1: y(t), y2: y(t), style: 'stroke: var(--grid); stroke-width: 1' }, svg);
      texto(svg, m.l - 6, y(t) + 3.5, fy(t), { 'text-anchor': 'end', class: 'g-tick' });
    });
    ticksBonitos(cfg.x.dominio[0], cfg.x.dominio[1], cfg.x.ticks || 4).forEach(function (t) {
      texto(svg, x(t), H - m.b + 14, fx(t), { 'text-anchor': 'middle', class: 'g-tick' });
    });
    el('line', { x1: m.l, x2: A - m.r, y1: H - m.b, y2: H - m.b, style: 'stroke: var(--axis); stroke-width: 1' }, svg);
    if (cfg.x.titulo) texto(svg, (m.l + A - m.r) / 2, H - 8, cfg.x.titulo, { 'text-anchor': 'middle', class: 'g-xtit' });
    if (cfg.y.titulo) texto(svg, m.l, m.t - 12, cfg.y.titulo, { class: 'g-ytit' });
    cfg.puntos.forEach(function (p) {
      var cx = x(p.x), cy = y(p.y);
      el('circle', { cx: cx, cy: cy, r: 7, style: 'fill: var(--surface-1)' }, svg);
      el('circle', { cx: cx, cy: cy, r: 5, style: p.hueco ? 'fill: var(--surface-1); stroke:' + p.color + '; stroke-width: 2' : 'fill:' + p.color }, svg);
      if (p.etiqueta) texto(svg, cx + (p.dx === undefined ? 8 : p.dx), cy + (p.dy === undefined ? 3.5 : p.dy), p.etiqueta, { 'text-anchor': p.ancla || 'start', class: p.fuerte ? 'g-val g-fuerte' : 'g-val' });
      if (cfg.interactivo) {
        var hit = el('circle', { cx: cx, cy: cy, r: 12, style: 'fill: transparent', tabindex: 0 }, svg);
        hit.addEventListener('pointermove', function (ev) {
          mostrarTip(ev, [{ color: p.color, valor: fy(p.y), nombre: cfg.y.corto || 'y' }, { valor: fx(p.x), nombre: cfg.x.corto || 'x' }], p.etiqueta);
        });
        hit.addEventListener('pointerleave', ocultarTip);
      }
    });
    if (cfg.nota) {
      String(cfg.nota).split('\n').forEach(function (ln, k) { texto(svg, m.l + 6, m.t + 12 + k * 13, ln, { class: k ? 'g-nota' : 'g-nota g-fuerte' }); });
    }
    return svg;
  }

  // Tabla equivalente de un gráfico (vista accesible).
  function tabla(cont, encabezados, filas) {
    var t = document.createElement('table'); t.className = 'g-tabla';
    var th = document.createElement('thead'), tr = document.createElement('tr');
    encabezados.forEach(function (h) { var c = document.createElement('th'); c.textContent = h; tr.appendChild(c); });
    th.appendChild(tr); t.appendChild(th);
    var tb = document.createElement('tbody');
    filas.forEach(function (f) {
      var r = document.createElement('tr');
      f.forEach(function (v, i) { var c = document.createElement('td'); c.textContent = v; if (i > 0 && /^[-+\d.,\s%M]+$/.test(String(v))) c.className = 'num'; r.appendChild(c); });
      tb.appendChild(r);
    });
    t.appendChild(tb);
    cont.textContent = '';
    cont.appendChild(t);
    return t;
  }

  global.G = { lineas: lineas, barras: barras, dispersion: dispersion, tabla: tabla, fmt: fmt, el: el, texto: texto, ocultarTip: ocultarTip };
})(window);
