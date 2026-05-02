const STORAGE_KEY='leonFiguritasV3';
const DB0={friendNickname:'',leonHave:[],leonRepeated:[],leonMissing:[],friendRepeated:[],friendMissing:[],history:[]};
const META={
  leonHave:{title:'Tengo de León'},leonRepeated:{title:'Repetidas de León'},leonMissing:{title:'Faltantes de León'},
  friendRepeated:{title:'Repetidas del amigo'},friendMissing:{title:'Faltantes del amigo'}
};
let db=loadDB();
let rec={receive:[],give:[]};

function loadDB(){try{return {...DB0,...JSON.parse(localStorage.getItem(STORAGE_KEY)||'{}')}}catch{return {...DB0}}}
function saveDB(){localStorage.setItem(STORAGE_KEY,JSON.stringify(db));}
const $=id=>document.getElementById(id);
function status(msg,ok=true){const e=$('status');e.textContent=msg;e.className=`status ${ok?'ok':''}`;}

function renderEditors(){
  $('leonLists').innerHTML=['leonHave','leonRepeated','leonMissing'].map(k=>editorHtml(k)).join('');
  $('friendLists').innerHTML=['friendRepeated','friendMissing'].map(k=>editorHtml(k)).join('');
  bindEditorEvents();
  ['leonHave','leonRepeated','leonMissing','friendRepeated','friendMissing'].forEach(k=>renderList(k,[]));
  $('friendNickname').value=db.friendNickname||'';
}
function editorHtml(key){
  return `<div class="listbox"><h3>${META[key].title}</h3>
  <textarea id="${key}Input" rows="6" placeholder="Pegá texto"></textarea>
  <button data-a="save" data-k="${key}">Normalizar y guardar</button>
  <button class="secondary" data-a="load" data-k="${key}">Editar cargando guardado</button>
  <button class="danger" data-a="clear" data-k="${key}">Borrar lista</button>
  <p>Total: <span id="${key}Total">0</span></p>
  <textarea id="${key}Flat" rows="2" readonly></textarea>
  <pre id="${key}Grouped"></pre>
  <ul id="${key}Issues"></ul></div>`;
}
function bindEditorEvents(){
  document.querySelectorAll('[data-a="save"]').forEach(b=>b.onclick=()=>saveList(b.dataset.k));
  document.querySelectorAll('[data-a="load"]').forEach(b=>b.onclick=()=>$(`${b.dataset.k}Input`).value=(db[b.dataset.k]||[]).join('\n'));
  document.querySelectorAll('[data-a="clear"]').forEach(b=>b.onclick=()=>{db[b.dataset.k]=[];saveDB();renderList(b.dataset.k,[]);status('Lista borrada.');});
}

function normalize(raw){
  const lines=raw.split(/\n+/).map(x=>x.trim()).filter(Boolean);const out=new Set();const issues=[];let current='';
  for(const line0 of lines){
    let line=line0.toUpperCase().replace(/\s+/g,' ').trim();
    const c=line.match(/^([A-Z]{3})(.*)$/);
    if(c){current=c[1];line=c[2]||'';} else if(!current){issues.push(`No interpretado: "${line0}"`);continue;}
    const nums=(line.replace(/[:]/g,' ').match(/\d+/g)||[]).map(n=>parseInt(n,10));
    if(!nums.length){issues.push(`Sin números: "${line0}"`);continue;}
    for(const n of nums){if(n<1||n>20){issues.push(`Fuera de rango ${n} en "${line0}"`);continue;} out.add(`${current}-${n}`);}
  }
  const list=[...out].sort((a,b)=>a.localeCompare(b,undefined,{numeric:true}));
  return {list,issues};
}

function renderList(key,issues){
  const list=db[key]||[];$(`${key}Total`).textContent=list.length;$(`${key}Flat`).value=list.join(', ');
  const g={};for(const c of list){const[p,n]=c.split('-');(g[p]??=[]).push(+n);} Object.keys(g).forEach(p=>g[p].sort((a,b)=>a-b));
  $(`${key}Grouped`).textContent=Object.keys(g).sort().map(p=>`${p}: ${g[p].join(', ')}`).join('\n')||'Sin datos';
  $(`${key}Issues`).innerHTML=(issues||[]).map(i=>`<li>${i}</li>`).join('')||'<li>Sin dudosas</li>';
}

function saveList(key){const p=normalize($(`${key}Input`).value);db[key]=p.list;db.friendNickname=$('friendNickname').value.trim();saveDB();renderList(key,p.issues);status(`${META[key].title} guardada.`);findTrades();}

function findTrades(){
  rec.receive=db.friendRepeated.filter(x=>db.leonMissing.includes(x)).sort();
  rec.give=db.leonRepeated.filter(x=>db.friendMissing.includes(x)).sort();
  $('receiveCount').textContent=rec.receive.length;$('giveCount').textContent=rec.give.length;
  $('tradeSummary').textContent=rec.receive.length||rec.give.length?`Cambio posible. ${rec.receive.length===rec.give.length?'Equilibrado':'No equilibrado'}`:'No hay coincidencias';
  $('receiveOptions').innerHTML=rec.receive.map(x=>`<label class="opt"><input type="checkbox" data-t="r" value="${x}"> ${x}</label>`).join('')||'<p>-</p>';
  $('giveOptions').innerHTML=rec.give.map(x=>`<label class="opt"><input type="checkbox" data-t="g" value="${x}"> ${x}</label>`).join('')||'<p>-</p>';
}

function confirmTrade(){
  const receive=[...document.querySelectorAll('input[data-t="r"]:checked')].map(x=>x.value);
  const give=[...document.querySelectorAll('input[data-t="g"]:checked')].map(x=>x.value);
  if(!receive.length&&!give.length)return status('Seleccioná figuritas para confirmar.',false);
  db.leonMissing=db.leonMissing.filter(x=>!receive.includes(x));
  db.leonHave=[...new Set([...db.leonHave,...receive])].sort((a,b)=>a.localeCompare(b,undefined,{numeric:true}));
  db.leonRepeated=db.leonRepeated.filter(x=>!give.includes(x));
  db.history.unshift({date:new Date().toISOString(),friend:db.friendNickname||'Amigo',received:receive,given:give,undo:{addMissing:receive,addRepeated:give,removeHave:receive}});
  saveDB();refreshAll();status('Cambio confirmado.');
}

function undoLast(){
  const h=db.history[0];if(!h)return status('No hay cambios para deshacer.',false);
  db.leonMissing=[...new Set([...db.leonMissing,...(h.undo?.addMissing||[])])].sort((a,b)=>a.localeCompare(b,undefined,{numeric:true}));
  db.leonRepeated=[...new Set([...db.leonRepeated,...(h.undo?.addRepeated||[])])].sort((a,b)=>a.localeCompare(b,undefined,{numeric:true}));
  db.leonHave=db.leonHave.filter(x=>!(h.undo?.removeHave||[]).includes(x));
  db.history.shift();saveDB();refreshAll();status('Último cambio deshecho.');
}

function renderHistory(){
  $('historyList').innerHTML=db.history.map(h=>`<div class="item"><b>${new Date(h.date).toLocaleString()}</b><br>Amigo: ${h.friend}<br>León recibió: ${h.received.join(', ')||'nada'}<br>León entregó: ${h.given.join(', ')||'nada'}</div>`).join('')||'<p>Sin historial.</p>';
}

function copyBackup(){const text=JSON.stringify({leonHave:db.leonHave,leonRepeated:db.leonRepeated,leonMissing:db.leonMissing,history:db.history},null,2);navigator.clipboard.writeText(text).then(()=>status('Backup copiado.')).catch(()=>status('No se pudo copiar.',false));}
function importBackup(){try{const x=JSON.parse($('backupInput').value);db.leonHave=Array.isArray(x.leonHave)?x.leonHave:[];db.leonRepeated=Array.isArray(x.leonRepeated)?x.leonRepeated:[];db.leonMissing=Array.isArray(x.leonMissing)?x.leonMissing:[];db.history=Array.isArray(x.history)?x.history:[];saveDB();refreshAll();status('Backup importado.');}catch{status('JSON inválido.',false);}}

function exportExcel(){
  if(typeof XLSX==='undefined') return status('No se cargó SheetJS.',false);
  const wb=XLSX.utils.book_new();
  const all=[...new Set([...db.leonHave,...db.leonMissing,...db.leonRepeated])].sort((a,b)=>a.localeCompare(b,undefined,{numeric:true}));
  const mis=all.map((c,i)=>({"N°":i+1,"Equipo / sección":c,"Estado":db.leonRepeated.includes(c)?'Repetida':db.leonMissing.includes(c)?'Falta':'Tengo',"Repetidas":db.leonRepeated.includes(c)?1:0,"Prioridad":db.leonMissing.includes(c)?'Alta':'Media',"Notas":"","Código para compartir":`${db.leonRepeated.includes(c)?'Repetida':db.leonMissing.includes(c)?'Falta':'Tengo'} ${c}`}));
  XLSX.utils.book_append_sheet(wb,XLSX.utils.json_to_sheet(mis),'Mis figuritas');
  const amigos=[{"Amigo":db.friendNickname||'','Tiene repetida':db.friendRepeated.join(', '),'Le falta':db.friendMissing.join(', '),'Coincide para cambio':rec.receive.concat(rec.give).join(', '),'Estado':rec.receive.length||rec.give.length?'Activo':'Sin match','Notas':'','Fecha':new Date().toLocaleDateString()}];
  XLSX.utils.book_append_sheet(wb,XLSX.utils.json_to_sheet(amigos),'Amigos');
  const ints=db.history.map(h=>({Fecha:new Date(h.date).toLocaleString(),Amigo:h.friend,'Yo entrego':h.given.join(', '),'Yo recibo':h.received.join(', '),Estado:'Confirmado','Lugar/medio':'','Notas':'','Valoración':''}));
  XLSX.utils.book_append_sheet(wb,XLSX.utils.json_to_sheet(ints),'Intercambios');
  const dash=[{Métrica:'Total tengo',Valor:db.leonHave.length},{Métrica:'Total faltantes',Valor:db.leonMissing.length},{Métrica:'Total repetidas',Valor:db.leonRepeated.length},{Métrica:'Total cambios',Valor:db.history.length},{Métrica:'Último cambio',Valor:db.history[0]?new Date(db.history[0].date).toLocaleString():'-'}];
  XLSX.utils.book_append_sheet(wb,XLSX.utils.json_to_sheet(dash),'Dashboard');
  const instr=[{Instrucción:'1) Pegá texto en cada lista y guardá.'},{Instrucción:'2) Cargá listas de amigo y buscá cambios.'},{Instrucción:'3) Seleccioná checks y confirmá.'},{Instrucción:'4) Usá backup y exportar Excel.'}];
  XLSX.utils.book_append_sheet(wb,XLSX.utils.json_to_sheet(instr),'Instrucciones');
  XLSX.writeFile(wb,'tracker_figuritas_mundial_2026.xlsx');
  status('Excel exportado.');
}

function refreshAll(){renderEditors();renderHistory();findTrades();}

$('friendNickname').addEventListener('change',()=>{db.friendNickname=$('friendNickname').value.trim();saveDB();});
$('findTradesBtn').onclick=findTrades;$('confirmTradeBtn').onclick=confirmTrade;$('undoTradeBtn').onclick=undoLast;
$('clearHistoryBtn').onclick=()=>{db.history=[];saveDB();renderHistory();status('Historial borrado.');};
$('copyBackupBtn').onclick=copyBackup;$('importBackupBtn').onclick=importBackup;$('exportExcelBtn').onclick=exportExcel;
refreshAll();
