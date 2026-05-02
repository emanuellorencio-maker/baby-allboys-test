const refs = {
  listType: document.getElementById('listType'),
  textInput: document.getElementById('textInput'),
  parseBtn: document.getElementById('parseBtn'),
  saveBtn: document.getElementById('saveBtn'),
  compareBtn: document.getElementById('compareBtn'),
  status: document.getElementById('status'),
  totalCount: document.getElementById('totalCount'),
  detectedList: document.getElementById('detectedList'),
  grouped: document.getElementById('grouped'),
  flatOutput: document.getElementById('flatOutput'),
  issues: document.getElementById('issues'),
  comparison: document.getElementById('comparison')
};

const STORAGE_KEY = 'leonFiguritasListsV1';

function normalizeInput(raw) {
  const lines = raw.split(/\n+/).map(l => l.trim()).filter(Boolean);
  const detected = new Set();
  const grouped = {};
  const issues = [];

  for (const line of lines) {
    const upper = line.toUpperCase().replace(/\s+/g, ' ').trim();
    const countryMatch = upper.match(/^([A-Z]{3})\s*[:\-\s]\s*(.+)$/);
    if (countryMatch) {
      const [, country, rest] = countryMatch;
      processCountryNumbers(country, rest, detected, grouped, issues, line);
      continue;
    }

    const packed = upper.match(/^([A-Z]{3})(?:\s*[-\s]\s*|\s+)([0-9\-,\s]+)$/);
    if (packed) {
      processCountryNumbers(packed[1], packed[2], detected, grouped, issues, line);
      continue;
    }

    issues.push(`No interpretado: "${line}"`);
  }

  return { detected: [...detected], grouped, issues };
}

function processCountryNumbers(country, rawNums, detected, grouped, issues, originalLine) {
  if (!/^[A-Z]{3}$/.test(country)) {
    issues.push(`Código país inválido en: "${originalLine}"`);
    return;
  }
  const nums = rawNums.split(/[\-,\s]+/).filter(Boolean);
  if (!nums.length) {
    issues.push(`Sin números en: "${originalLine}"`);
    return;
  }
  for (const n of nums) {
    const value = Number.parseInt(n, 10);
    if (!Number.isInteger(value) || value < 1 || value > 20) {
      issues.push(`Número fuera de rango (${n}) en: "${originalLine}"`);
      continue;
    }
    const code = `${country}-${value}`;
    if (detected.has(code)) continue;
    detected.add(code);
    if (!grouped[country]) grouped[country] = [];
    grouped[country].push(value);
  }
}

function renderResult(result) {
  refs.totalCount.textContent = String(result.detected.length);
  refs.detectedList.innerHTML = result.detected.map(c => `<li>${c}</li>`).join('') || '<li>Sin resultados</li>';

  const groupLines = Object.keys(result.grouped)
    .sort()
    .map(k => `${k}: ${result.grouped[k].sort((a,b)=>a-b).join(', ')}`);
  refs.grouped.textContent = groupLines.join('\n') || 'Sin datos';
  refs.flatOutput.value = result.detected.join(', ');
  refs.issues.innerHTML = result.issues.map(i => `<li>${i}</li>`).join('') || '<li>Sin errores</li>';
}

function saveCurrent() {
  const parsed = normalizeInput(refs.textInput.value);
  const db = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
  db[refs.listType.value] = parsed.detected;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(db));
  refs.status.textContent = 'Lista guardada localmente en este navegador.';
}

function compareWithOther() {
  const db = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
  const currentType = refs.listType.value;
  const current = new Set((db[currentType] || []));
  const otherKey = Object.keys(db).find(k => k !== currentType && (db[k] || []).length);
  if (!otherKey) {
    refs.comparison.innerHTML = '<p>No hay otra lista guardada para comparar.</p>';
    return;
  }
  const other = new Set(db[otherKey]);
  const onlyCurrent = [...current].filter(x => !other.has(x));
  const onlyOther = [...other].filter(x => !current.has(x));
  refs.comparison.innerHTML = `
    <h3>Comparación con: ${otherKey}</h3>
    <p>Solo en ${currentType}: ${onlyCurrent.join(', ') || 'ninguna'}</p>
    <p>Solo en ${otherKey}: ${onlyOther.join(', ') || 'ninguna'}</p>
  `;
}

refs.parseBtn.addEventListener('click', () => {
  const parsed = normalizeInput(refs.textInput.value);
  renderResult(parsed);
  refs.status.textContent = 'Normalización completada.';
});
refs.saveBtn.addEventListener('click', saveCurrent);
refs.compareBtn.addEventListener('click', compareWithOther);
