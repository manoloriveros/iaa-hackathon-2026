// Notas locales para una revisión real; no modifica el acta ni cierra hallazgos.
(function () {
  const packet = D.revision_preparada;
  const evidenceLink = (rel, label) => {
    const href = rel.startsWith('docs/') ? rel.slice(5) : '../' + rel;
    return `<a href="${esc(href)}">${esc(label || rel)}</a>`;
  };
  const labels = {
    'GOV-007': 'Corrección técnica del paquete 1.2 aceptada',
    'GOV-008': 'Corrección técnica de la captura 1.1.2 aceptada',
    'MOD-002': 'Suficiencia de reservas como limitación aceptada',
    'GOV-003': 'Ausencia de réplica independiente como limitación aceptada',
    'R01': 'Alcance del concurso aceptado con hipótesis de consistencia'
  };
  const previous = D.revision_humana.decisiones_especificas || {};
  $('decisionesregistradas').innerHTML = table(
    ['Asunto', 'Decisión ya registrada', 'Fecha y alcance'],
    Object.entries(previous).map(([id, x]) => [
      esc(id), esc(labels[id] || x.decision),
      `${esc(x.fecha)}<br>${esc(x.alcance || 'Aceptación técnica específica; revisión general separada.')}<br>${evidenceLink(x.registro, 'Registro original')}`
    ])
  );
  const key = 'iaa2026-revision-decisiones-v2-' + packet.sha256_csv;
  let notes = { revisor: packet.revisor_designado, fecha_revision: '', alcance: '', items: {} };
  try {
    const old = JSON.parse(localStorage.getItem(key));
    if (old && typeof old === 'object' && !Array.isArray(old)) {
      notes = { ...notes, ...old, items: old.items || {} };
    }
  } catch {}
  $('revisor').value = notes.revisor || '';
  $('fecharevision').value = notes.fecha_revision || '';
  $('alcancerevision').value = notes.alcance || '';
  function save() {
    notes.revisor = $('revisor').value.trim();
    notes.fecha_revision = $('fecharevision').value;
    notes.alcance = $('alcancerevision').value.trim();
    notes.corte_fuentes = D.generado_utc;
    notes.ultima_edicion = new Date().toISOString();
    try {
      localStorage.setItem(key, JSON.stringify(notes));
      $('notasestado').textContent = 'Notas guardadas en este navegador. Exportarlas conserva tu respuesta; no cambia el acta automáticamente.';
    } catch {
      $('notasestado').textContent = 'El navegador no permite guardar notas aquí. El botón de exportación sigue disponible.';
    }
  }
  $('revisionlista').innerHTML = packet.preguntas.map(q => `
    <div class="review-row">
      <div class="review-top"><label for="status-${q.id}">${esc(q.id)} · ${esc(q.tema)}</label>
      <select id="status-${q.id}" aria-label="Tu decisión sobre ${esc(q.tema)}">
        <option value="">Pendiente de tu respuesta</option>
        ${q.opciones_sin_preseleccion.map(o => `<option value="${esc(o)}">${esc(o)}</option>`).join('')}
      </select></div>
      <p>${esc(q.pregunta)}</p><p class="source">${esc(q.alcance)}</p>
      ${q.decision && q.fecha ? `<p class="source">Decisión registrada: ${esc(q.fecha)}. ${evidenceLink(q.registro_decision, 'Ver tu decisión literal')}</p>` : ''}
      <p class="source">${q.evidencia.map(e => evidenceLink(e)).join(' · ')}</p>
      <label for="note-${q.id}">Motivo, evidencia leída y corrección que pides</label>
      <textarea id="note-${q.id}" placeholder="Escribe tu revisión de este punto"></textarea>
    </div>`).join('');
  packet.preguntas.forEach(q => {
    const item = notes.items[q.id] || {};
    const select = $('status-' + q.id), note = $('note-' + q.id);
    if (q.decision && q.fecha) {
      select.value = q.decision;
      note.value = q.texto_literal || q.motivo || '';
      select.disabled = true;
      note.disabled = true;
      return; // Las notas locales no sustituyen una decisión ya registrada.
    }
    select.value = q.opciones_sin_preseleccion.includes(item.decision) ? item.decision : '';
    note.value = typeof item.motivo === 'string' ? item.motivo : '';
    const update = () => {
      notes.items[q.id] = { decision: select.value || null, motivo: note.value.trim() || null };
      save();
    };
    select.addEventListener('input', update);
    note.addEventListener('input', update);
  });
  ['revisor', 'fecharevision', 'alcancerevision'].forEach(id => $(id).addEventListener('input', save));
  $('exportar').addEventListener('click', () => {
    save();
    const hasDecision = Object.values(notes.items).some(x => x && x.decision);
    if (hasDecision && (!notes.revisor || !notes.fecha_revision || !notes.alcance)) {
      $('notasestado').textContent = 'Para exportar decisiones, completa tu nombre, la fecha de revisión y el alcance. Las opciones sin responder siguen pendientes.';
      return;
    }
    const payload = {
      tipo: 'Notas del participante para contrastar antes de registrar la revisión general',
      candidato: packet.candidato, sha256_csv: packet.sha256_csv,
      plantilla: 'registro/revision_preparada_20261020.json',
      decisiones_anteriores: previous, fuentes: D.fuentes, ...notes,
      firma_o_evidencia_humana: null, actualizacion_automatica_del_acta: false
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob), anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = 'revision-S30-' + new Date().toISOString().slice(0, 10) + '.json';
    anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
  });
})();
