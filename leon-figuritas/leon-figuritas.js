let db=JSON.parse(localStorage.getItem("db")||"{}")

function parse(txt){
return txt.toUpperCase().split(/[\n, ]+/).filter(x=>x.includes("-")||x.match(/[A-Z]{3}\d+/)).map(x=>{
if(x.includes("-"))return x
return x.replace(/([A-Z]{3})(\d+)/,"$1-$2")
})
}

function buscar(){
let r=parse(repesA.value)
let f=parse(faltan.value)
let e=parse(repes.value)
let fa=parse(faltanA.value)

let recibe=r.filter(x=>f.includes(x))
let entrega=e.filter(x=>fa.includes(x))

document.getElementById("recibe").innerText=recibe.join(", ")
document.getElementById("entrega").innerText=entrega.join(", ")

window._recibe=recibe
window._entrega=entrega
}

function confirmar(){
let recibe=window._recibe||[]
let entrega=window._entrega||[]

db.historial=db.historial||[]
db.historial.unshift({fecha:new Date(),recibe,entrega})

localStorage.setItem("db",JSON.stringify(db))
renderHist()
}

function guardar(){
db.repes=parse(repes.value)
db.faltan=parse(faltan.value)
localStorage.setItem("db",JSON.stringify(db))
}

function renderHist(){
let h=db.historial||[]
document.getElementById("historial").innerHTML=h.map(x=>JSON.stringify(x)).join("<br>")
}

renderHist()
