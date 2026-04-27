const CATEGORIAS=["2013","2014","2015","2016","2017","2018","2019","2020","2021","2022"];
const TIRAS=["All Boys A","All Boys B","Los Albos","All Boys"];
const INSTANCIAS=["Grupos","32avos","Octavos","Cuartos","Semifinal","Tercer puesto","Final"];
const state={participantes:[],partidos:[],ranking:[],vista:"general",busqueda:"",categoria:"",tira:"",grupo:"",fecha:"",instancia:"",seleccion:""};

const $=sel=>document.querySelector(sel);
const byId=id=>document.getElementById(id);
const esc=v=>String(v??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]));
const norm=v=>String(v||"").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().trim();

function obtenerResultadoPartido(partido){
  if(!partido||partido.estado!=="finalizado")return null;
  const gl=partido.resultado_real?.goles_local;
  const gv=partido.resultado_real?.goles_visitante;
  if(!Number.isFinite(gl)||!Number.isFinite(gv))return null;
  if(gl>gv)return "L";
  if(gl<gv)return "V";
  return "E";
}

function signo(l,v){
  if(!Number.isFinite(l)||!Number.isFinite(v))return null;
  if(l>v)return "L";
  if(l<v)return "V";
  return "E";
}

function calcularPuntos(pronostico,partido){
  if(!partido){
    console.warn("Pronostico con partido inexistente:",pronostico?.partido_id);
    return {puntos:0,estado:"pendiente"};
  }
  const real=obtenerResultadoPartido(partido);
  if(!real)return {puntos:0,estado:"pendiente"};
  const gl=pronostico?.goles_local;
  const gv=pronostico?.goles_visitante;
  if(!Number.isFinite(gl)||!Number.isFinite(gv))return {puntos:0,estado:"pendiente"};
  if(gl===partido.resultado_real.goles_local&&gv===partido.resultado_real.goles_visitante)return {puntos:3,estado:"exacto"};
  if(signo(gl,gv)===real)return {puntos:1,estado:"simple"};
  return {puntos:0,estado:"error"};
}

function calcularRanking(participantes=state.participantes){
  const partidosMap=new Map(state.partidos.map(p=>[p.id,p]));
  const filas=participantes.map(p=>{
    const detalle=(p.pronosticos||[]).map(pr=>{
      const partido=partidosMap.get(pr.partido_id);
      const calc=calcularPuntos(pr,partido);
      return {pronostico:pr,partido,...calc};
    });
    const exactos=detalle.filter(x=>x.estado==="exacto").length;
    const simples=detalle.filter(x=>x.estado==="simple").length;
    const errores=detalle.filter(x=>x.estado==="error").length;
    const pendientes=detalle.filter(x=>x.estado==="pendiente").length;
    const puntos=detalle.reduce((acc,x)=>acc+x.puntos,0);
    return {...p,detalle,puntos,exactos,simples,errores,pendientes};
  }).sort((a,b)=>b.puntos-a.puntos||b.exactos-a.exactos||b.simples-a.simples||a.errores-b.errores||a.apellido.localeCompare(b.apellido,"es")||a.nombre.localeCompare(b.nombre,"es"));
  filas.forEach((p,i)=>p.puesto=i+1);
  return filas;
}

function mejorPor(campo,valor){
  return state.ranking.filter(p=>p[campo]===valor).sort((a,b)=>a.puesto-b.puesto)[0];
}

function frases(p){
  if(!p)return "";
  if(p.puesto===1)return "El que manda en el Mundial";
  if(p.puesto<=3)return "Zona de podio";
  if(p.puesto<=10)return "Metido en la pelea";
  return "Todavia hay tiempo para remontar";
}

function badges(p){
  const out=[];
  if(p.puesto===1)out.push("🥇 Puntero general");
  if(p.puesto<=3)out.push("🏁 Top 3");
  if(p.exactos>=2)out.push("🎯 Especialista en exactos");
  if((p.simples+p.exactos)>=3)out.push("🔥 En racha");
  if(mejorPor("categoria",p.categoria)?.id===p.id)out.push("⚽ Mejor de su categoria");
  return out;
}

function filtrarRanking(){
  const q=norm(state.busqueda);
  let rows=[...state.ranking];
  if(q)rows=rows.filter(p=>norm(`${p.nombre} ${p.apellido} ${p.nombre_hijo}`).includes(q));
  if(state.categoria)rows=rows.filter(p=>p.categoria===state.categoria);
  if(state.tira)rows=rows.filter(p=>p.tira===state.tira);
  if(state.grupo||state.fecha||state.instancia||state.seleccion){
    rows=rows.filter(p=>p.detalle.some(d=>{
      const m=d.partido;
      if(!m)return false;
      if(state.grupo&&m.grupo!==state.grupo)return false;
      if(state.fecha&&m.fecha!==state.fecha)return false;
      if(state.instancia&&m.instancia!==state.instancia)return false;
      if(state.seleccion&&m.equipo_local!==state.seleccion&&m.equipo_visitante!==state.seleccion)return false;
      return true;
    }));
  }
  if(state.vista==="categorias"&&state.categoria)rows=rows.filter(p=>p.categoria===state.categoria);
  if(state.vista==="tiras"&&state.tira)rows=rows.filter(p=>p.tira===state.tira);
  if(state.vista==="exactos")rows.sort((a,b)=>b.exactos-a.exactos||b.puntos-a.puntos||a.puesto-b.puesto);
  if(state.vista==="simples")rows.sort((a,b)=>b.simples-a.simples||b.puntos-a.puntos||a.puesto-b.puesto);
  if(state.vista==="familia")rows.sort((a,b)=>a.categoria.localeCompare(b.categoria)||a.puesto-b.puesto);
  return rows;
}

function renderResumen(){
  const total=state.participantes.length;
  const finalizados=state.partidos.filter(p=>p.estado==="finalizado").length;
  const lider=state.ranking[0];
  const porCategoria=CATEGORIAS.map(cat=>({cat,total:state.ranking.filter(p=>p.categoria===cat).reduce((a,p)=>a+p.puntos,0)})).sort((a,b)=>b.total-a.total)[0];
  const promedio=total?(state.ranking.reduce((a,p)=>a+p.puntos,0)/total).toFixed(1):"0.0";
  byId("resumenProde").innerHTML=[
    ["Participantes",total],
    ["Partidos cargados",state.partidos.length],
    ["Finalizados",finalizados],
    ["Lider actual",lider?`${lider.nombre} ${lider.apellido}`:"Pendiente"],
    ["Categoria picante",porCategoria?.cat||"-"],
    ["Promedio puntos",promedio]
  ].map(([label,value])=>`<article class="summary-card"><span>${esc(label)}</span><strong>${esc(value)}</strong></article>`).join("");
}

function renderFiltros(){
  const grupos=[...new Set(state.partidos.map(p=>p.grupo).filter(Boolean))];
  const fechas=[...new Set(state.partidos.map(p=>p.fecha).filter(Boolean))];
  const selecciones=[...new Set(state.partidos.flatMap(p=>[p.equipo_local,p.equipo_visitante]).filter(t=>t&&t!=="Pendiente"))].sort();
  byId("tabsRanking").innerHTML=[
    ["general","General"],["categorias","Categorias"],["tiras","Tiras"],["exactos","Exactos"],["simples","Simples"],["familia","Mis datos"]
  ].map(([id,label])=>`<button class="tab-btn ${state.vista===id?"activo":""}" data-tab="${id}">${label}</button>`).join("");
  byId("filtrosProde").innerHTML=`
    ${select("categoria","Categoria",["",...CATEGORIAS],state.categoria)}
    ${select("tira","Tira",["",...TIRAS],state.tira)}
    ${select("grupo","Grupo",["",...grupos],state.grupo)}
    ${select("instancia","Instancia",["",...INSTANCIAS],state.instancia)}
    ${select("fecha","Fecha",["",...fechas],state.fecha)}
    ${select("seleccion","Seleccion",["",...selecciones],state.seleccion)}
    <button type="button" class="clear-btn" id="limpiarFiltros">Limpiar</button>
  `;
}

function select(id,label,items,value){
  return `<label class="filter-label"><span>${label}</span><select id="${id}">${items.map(x=>`<option value="${esc(x)}" ${x===value?"selected":""}>${x?esc(x):"Todos"}</option>`).join("")}</select></label>`;
}

function renderRanking(){
  const rows=filtrarRanking();
  byId("tituloRanking").textContent={general:"General",categorias:"Ranking por categoria",tiras:"Ranking por tira",exactos:"Ranking de exactos",simples:"Aciertos simples",familia:"Buscar participante"}[state.vista]||"General";
  if(!state.participantes.length){
    byId("rankingLista").innerHTML='<div class="empty">Todavia no hay participantes cargados.</div>';
    return;
  }
  const finalizados=state.partidos.some(p=>p.estado==="finalizado");
  if(!rows.length){
    byId("rankingLista").innerHTML='<div class="empty">No hay participantes para esos filtros.</div>';
    return;
  }
  byId("rankingLista").innerHTML=`${!finalizados?'<div class="empty">El ranking se actualizara cuando haya resultados cargados.</div>':""}${rows.map(p=>`
    <button type="button" class="rank-card ${p.puesto===1?"top1":""}" data-id="${esc(p.id)}">
      <span class="place">${p.puesto<=3?["","🥇","🥈","🥉"][p.puesto]:"#"+p.puesto}</span>
      <span class="who"><strong>${esc(p.apellido)}, ${esc(p.nombre)}</strong><span>Hijo: ${esc(p.nombre_hijo)} · ${esc(p.categoria)} · ${esc(p.tira)}</span><span class="stats-mini">Exactos ${p.exactos} · Simples ${p.simples} · Errores ${p.errores} · Pendientes ${p.pendientes}</span></span>
      <span class="points"><strong>${p.puntos}</strong><span>pts</span></span>
      <span class="badges">${badges(p).map(b=>`<span class="badge">${esc(b)}</span>`).join("")}</span>
    </button>
  `).join("")}`;
}

function renderCardViral(){
  const p=filtrarRanking()[0]||state.ranking[0];
  byId("cardViral").innerHTML=p?`
    <div class="viral-rank"><div><span>Puesto</span><strong>#${p.puesto}</strong></div><div class="points"><strong>${p.puntos}</strong><span>pts</span></div></div>
    <div class="viral-name">${esc(p.nombre)} ${esc(p.apellido)}</div>
    <div class="viral-meta">${esc(p.categoria)} · ${esc(p.tira)} · Hijo: ${esc(p.nombre_hijo)}</div>
    <div class="viral-phrase">${esc(frases(p))}</div>
  `:'<div class="empty">Card lista cuando haya participantes.</div>';
}

function renderDetalleParticipante(id){
  const p=state.ranking.find(x=>x.id===id);
  if(!p)return;
  const catRank=state.ranking.filter(x=>x.categoria===p.categoria).findIndex(x=>x.id===p.id)+1;
  const tiraRank=state.ranking.filter(x=>x.tira===p.tira).findIndex(x=>x.id===p.id)+1;
  byId("detalleParticipante").innerHTML=`
    <div class="detail-head">
      <p class="eyebrow">Detalle participante</p>
      <h3 id="modalTitulo">${esc(p.nombre)} ${esc(p.apellido)}</h3>
      <p>Hijo: ${esc(p.nombre_hijo)} · ${esc(p.categoria)} · ${esc(p.tira)}</p>
    </div>
    <div class="detail-grid">
      ${detail("Puesto general","#"+p.puesto)}${detail("Puesto categoria","#"+catRank)}${detail("Puesto tira","#"+tiraRank)}${detail("Puntos",p.puntos)}
      ${detail("Exactos",p.exactos)}${detail("Simples",p.simples)}${detail("Errores",p.errores)}${detail("Pendientes",p.pendientes)}
    </div>
    <button type="button" class="primary-action" data-share="${esc(p.id)}">Compartir mi puesto</button>
    <div class="prediction-list">${p.detalle.map(d=>renderPrediccion(d)).join("")}</div>
  `;
  byId("modalParticipante").classList.remove("oculto");
}

function detail(label,value){return `<div class="detail-stat"><span>${esc(label)}</span><strong>${esc(value)}</strong></div>`}

function renderPrediccion(d){
  const p=d.partido;
  const pr=d.pronostico;
  if(!p)return `<article class="prediction"><div class="prediction-top">Partido inexistente <span class="state-pendiente">Pendiente</span></div></article>`;
  const real=obtenerResultadoPartido(p)?`${p.resultado_real.goles_local}-${p.resultado_real.goles_visitante}`:"Pendiente";
  const estado={exacto:"Exacto",simple:"Acierto simple",error:"Error",pendiente:"Pendiente"}[d.estado];
  return `<article class="prediction">
    <div class="prediction-top"><span>${esc(p.equipo_local)} vs ${esc(p.equipo_visitante)}</span><span class="state-${d.estado}">${estado}</span></div>
    <div class="prediction-meta">${esc(p.fecha)} · ${esc(p.grupo||p.instancia)} · Pronostico ${pr.goles_local}-${pr.goles_visitante} · Real ${real} · ${d.puntos} pts</div>
  </article>`;
}

async function compartirPuesto(id){
  const p=state.ranking.find(x=>x.id===id)||state.ranking[0];
  if(!p)return;
  const text=`Estoy puesto #${p.puesto} en el Prode Mundial Baby All Boys ⚽🏆`;
  if(navigator.share){
    try{await navigator.share({title:"Prode Mundial Baby All Boys",text,url:location.href});return}catch(e){}
  }
  await navigator.clipboard?.writeText(text);
  alert("Mensaje copiado");
}

async function copiarMensaje(){
  const p=filtrarRanking()[0]||state.ranking[0];
  if(!p)return;
  const text=`Voy #${p.puesto} en el Prode Mundial Baby All Boys con ${p.puntos} puntos. ¿Quien me alcanza? ⚽🏆`;
  await navigator.clipboard?.writeText(text);
  alert("Mensaje copiado");
}

function bindEvents(){
  byId("buscador").addEventListener("input",e=>{state.busqueda=e.target.value;renderRanking();renderCardViral()});
  byId("tabsRanking").addEventListener("click",e=>{const btn=e.target.closest("[data-tab]");if(!btn)return;state.vista=btn.dataset.tab;renderFiltros();bindDynamicFilters();renderRanking();renderCardViral()});
  byId("rankingLista").addEventListener("click",e=>{const card=e.target.closest("[data-id]");if(card)renderDetalleParticipante(card.dataset.id)});
  byId("modalParticipante").addEventListener("click",e=>{if(e.target.closest("[data-close-modal]"))byId("modalParticipante").classList.add("oculto");const share=e.target.closest("[data-share]");if(share)compartirPuesto(share.dataset.share)});
  byId("btnCopiarMensaje").addEventListener("click",copiarMensaje);
  byId("btnCompartirLider").addEventListener("click",()=>compartirPuesto(state.ranking[0]?.id));
}

function bindDynamicFilters(){
  ["categoria","tira","grupo","fecha","instancia","seleccion"].forEach(id=>{
    byId(id)?.addEventListener("change",e=>{state[id]=e.target.value;renderRanking();renderCardViral()});
  });
  byId("limpiarFiltros")?.addEventListener("click",()=>{Object.assign(state,{busqueda:"",categoria:"",tira:"",grupo:"",fecha:"",instancia:"",seleccion:""});byId("buscador").value="";renderFiltros();bindDynamicFilters();renderRanking();renderCardViral()});
}

async function init(){
  try{
    const [participantes,partidos]=await Promise.all([
      fetch("data/prode/participantes.json").then(r=>{if(!r.ok)throw Error();return r.json()}),
      fetch("data/prode/partidos.json").then(r=>{if(!r.ok)throw Error();return r.json()})
    ]);
    state.participantes=Array.isArray(participantes)?participantes:[];
    state.partidos=Array.isArray(partidos)?partidos:[];
    state.ranking=calcularRanking();
    byId("estadoCarga").className="status-card ok";
    renderResumen();renderFiltros();renderRanking();renderCardViral();bindEvents();bindDynamicFilters();
  }catch(e){
    byId("estadoCarga").className="status-card error";
    byId("estadoCarga").textContent="No se pudieron cargar los datos del Prode.";
    console.error(e);
  }
}

init();
