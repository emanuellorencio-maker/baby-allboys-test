const STORAGE_KEY = 'leonFiguritasV2';
const EMPTY_DB = { friendName: '', leonRepeated: [], leonMissing: [], friendRepeated: [], friendMissing: [], history: [] };
const ids = {
  leonRepeated:{input:'leonRepeatedInput',total:'leonRepeatedTotal',grouped:'leonRepeatedGrouped',flat:'leonRepeatedFlat',issues:'leonRepeatedIssues'},
  leonMissing:{input:'leonMissingInput',total:'leonMissingTotal',grouped:'leonMissingGrouped',flat:'leonMissingFlat',issues:'leonMissingIssues'},
  friendRepeated:{input:'friendRepeatedInput',total:'friendRepeatedTotal',grouped:'friendRepeatedGrouped',flat:'friendRepeatedFlat',issues:'friendRepeatedIssues'},
  friendMissing:{input:'friendMissingInput',total:'friendMissingTotal',grouped:'friendMissingGrouped',flat:'friendMissingFlat',issues:'friendMissingIssues'}
};
let db = loadDB();
let currentRecommendations = { receive: [], give: [] };

function loadDB(){ try { return { ...EMPTY_DB, ...(JSON.parse(localStorage.getItem(STORAGE_KEY)||'{}')) }; } catch { return { ...EMPTY_DB }; } }
function saveDB(){ localStorage.setItem(STORAGE_KEY, JSON.stringify(db)); }
function byId(id){ return document.getElementById(id); }
function setStatus(msg, ok=true){ const el=byId('status'); el.textContent = msg; el.className = `status ${ok?'ok':''}`; }

function normalizeInput(raw){
  const lines = raw.split(/\n+/).map(x=>x.trim()).filter(Boolean); const detected=new Set(); const grouped={}; const issues=[];
  for(const line of lines){
    const up=line.toUpperCase().replace(/\s+/g,' ').trim();
    const m=up.match(/^([A-Z]{3})\s*[:\-\s]\s*(.+)$/);
    if(!m){ issues.push(`No interpretado: "${line}"`); continue; }
    const country=m[1]; const nums=m[2].split(/[\-,\s]+/).filter(Boolean);
    if(!/^[A-Z]{3}$/.test(country)){ issues.push(`Código inválido: "${line}"`); continue; }
    if(!nums.length){ issues.push(`Sin números: "${line}"`); continue; }
    for(const n of nums){
      const v=Number.parseInt(n,10);
      if(!Number.isInteger(v)||v<1||v>20){ issues.push(`Número fuera de rango (${n}) en: "${line}"`); continue; }
      const code=`${country}-${v}`; if(detected.has(code)) continue;
      detected.add(code); if(!grouped[country]) grouped[country]=[]; grouped[country].push(v);
    }
  }
  Object.keys(grouped).forEach(k=>grouped[k].sort((a,b)=>a-b));
  return { list:[...detected].sort(), grouped, issues };
}

function renderList(key, issues=[]){
  const map=ids[key], list=db[key]||[];
  byId(map.total).textContent=String(list.length);
  byId(map.flat).value=list.join(', ');
  const g={}; list.forEach(c=>{const [p,n]=c.split('-'); (g[p]??=[]).push(Number(n));});
  byId(map.grouped).textContent = Object.keys(g).sort().map(p=>`${p}: ${g[p].sort((a,b)=>a-b).join(', ')}`).join('\n') || 'Sin datos';
  byId(map.issues).innerHTML = issues.map(i=>`<li>${i}</li>`).join('') || '<li>Sin dudosas</li>';
}

function parseSave(key){
  const raw=byId(ids[key].input).value;
  const parsed=normalizeInput(raw);
  db[key]=parsed.list;
  db.friendName = byId('friendName').value.trim();
  saveDB(); renderList(key, parsed.issues); renderHistory();
  setStatus(`${key} guardada (${parsed.list.length}).`);
}

function loadIntoEditor(key){ byId(ids[key].input).value = (db[key]||[]).join('\n'); setStatus(`Se cargó ${key} para editar.`); }
function clearList(key){ db[key]=[]; saveDB(); renderList(key); setStatus(`${key} borrada.`); }

function findTrades(){
  const leonNeed=new Set(db.leonMissing); const friendRep=new Set(db.friendRepeated);
  const leonRep=new Set(db.leonRepeated); const friendNeed=new Set(db.friendMissing);
  currentRecommendations.receive=[...friendRep].filter(x=>leonNeed.has(x)).sort();
  currentRecommendations.give=[...leonRep].filter(x=>friendNeed.has(x)).sort();
  renderTradeOptions();
}

function renderTradeOptions(){
  const r=byId('receiveOptions'), g=byId('giveOptions'); r.innerHTML=''; g.innerHTML='';
  currentRecommendations.receive.forEach(code=>r.insertAdjacentHTML('beforeend',`<label class="option"><input type="checkbox" data-type="receive" value="${code}"> ${code}</label>`));
  currentRecommendations.give.forEach(code=>g.insertAdjacentHTML('beforeend',`<label class="option"><input type="checkbox" data-type="give" value="${code}"> ${code}</label>`));
  byId('receiveCount').textContent=String(currentRecommendations.receive.length);
  byId('giveCount').textContent=String(currentRecommendations.give.length);
  const total = currentRecommendations.receive.length + currentRecommendations.give.length;
  byId('tradeMessage').textContent = total ? 'Cambio posible' : 'No hay coincidencias por ahora';
  byId('balance').textContent = currentRecommendations.receive.length===currentRecommendations.give.length ? 'Está equilibrado.' : 'No está equilibrado.';
}

function confirmTrade(){
  const rec = [...document.querySelectorAll('input[data-type="receive"]:checked')].map(x=>x.value);
  const giv = [...document.querySelectorAll('input[data-type="give"]:checked')].map(x=>x.value);
  if(!rec.length && !giv.length){ setStatus('Seleccioná al menos una figurita.', false); return; }
  db.leonMissing = db.leonMissing.filter(x=>!rec.includes(x));
  db.leonRepeated = db.leonRepeated.filter(x=>!giv.includes(x));
  db.history.unshift({ date:new Date().toISOString(), friend: db.friendName || 'Amigo', received: rec, given: giv });
  saveDB(); renderAll(); setStatus('Cambio confirmado y guardado en historial.');
}

function renderHistory(){
  const el=byId('historyList');
  if(!db.history.length){ el.innerHTML='<p>Sin cambios guardados.</p>'; return; }
  el.innerHTML = db.history.map(h=>`<div class="history-item"><strong>${new Date(h.date).toLocaleString()}</strong><br>Amigo: ${h.friend}<br>León recibió: ${h.received.join(', ')||'nada'}<br>León entregó: ${h.given.join(', ')||'nada'}</div>`).join('');
}

function copyBackup(){
  const backup = JSON.stringify({ leonRepeated:db.leonRepeated, leonMissing:db.leonMissing, history:db.history }, null, 2);
  navigator.clipboard.writeText(backup).then(()=>setStatus('Backup copiado.')).catch(()=>setStatus('No se pudo copiar, copiá manualmente desde consola.', false));
}

function importBackup(){
  const txt=byId('backupInput').value.trim(); if(!txt){ setStatus('Pegá un JSON de backup.', false); return; }
  try{
    const data=JSON.parse(txt);
    db.leonRepeated=Array.isArray(data.leonRepeated)?data.leonRepeated:[];
    db.leonMissing=Array.isArray(data.leonMissing)?data.leonMissing:[];
    db.history=Array.isArray(data.history)?data.history:[];
    saveDB(); renderAll(); setStatus('Backup importado.');
  }catch{ setStatus('JSON inválido.', false); }
}

function clearFriend(){ db.friendName=''; db.friendRepeated=[]; db.friendMissing=[]; saveDB(); renderAll(); setStatus('Listas del amigo limpiadas.'); }
function clearHistory(){ db.history=[]; saveDB(); renderHistory(); setStatus('Historial borrado.'); }

function renderAll(){
  byId('friendName').value=db.friendName||'';
  Object.keys(ids).forEach(k=>renderList(k));
  renderHistory(); findTrades();
}

document.querySelectorAll('[data-action="parse-save"]').forEach(b=>b.addEventListener('click',()=>parseSave(b.dataset.key)));
document.querySelectorAll('[data-action="load"]').forEach(b=>b.addEventListener('click',()=>loadIntoEditor(b.dataset.key)));
document.querySelectorAll('[data-action="clear"]').forEach(b=>b.addEventListener('click',()=>clearList(b.dataset.key)));
byId('findTradesBtn').addEventListener('click', findTrades);
byId('confirmTradeBtn').addEventListener('click', confirmTrade);
byId('clearFriendBtn').addEventListener('click', clearFriend);
byId('clearHistoryBtn').addEventListener('click', clearHistory);
byId('copyBackupBtn').addEventListener('click', copyBackup);
byId('importBackupBtn').addEventListener('click', importBackup);
byId('friendName').addEventListener('change',()=>{db.friendName=byId('friendName').value.trim(); saveDB();});

renderAll();
