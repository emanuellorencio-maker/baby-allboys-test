import json
import os
import random
import re
import sys
import time
from typing import Dict, List, Optional, Tuple

try:
    import cloudscraper  # type: ignore
except Exception:
    cloudscraper = None

import requests
from bs4 import BeautifulSoup

ZONAS = {
    "c": {
        "url": "https://fefi.com.ar/2026-torneo-anual-baby-futbol/c/",
        "equipo": 'ALL BOYS "A"',
        "categorias": ["2019", "2013", "2018", "2014", "2017", "2016", "2015"],
    },
    "i": {
        "url": "https://fefi.com.ar/2026-torneo-anual-baby-futbol/i/",
        "equipo": 'ALL BOYS "B"',
        "categorias": ["2019", "2013", "2018", "2014", "2017", "2016", "2015"],
    },
    "mat1": {
        "url": "https://fefi.com.ar/2026-torneo-anual-baby-futbol/mat-1/",
        "equipo": "LOS ALBOS",
        "categorias": ["2013", "2014/15", "2016/17", "2018/19", "2020/21/22"],
    },
    "mat4": {
        "url": "https://fefi.com.ar/2026-torneo-anual-baby-futbol/mat-4/",
        "equipo": "ALL BOYS",
        "categorias": ["2013", "2014", "2015", "2016", "2017", "2018/19/20"],
    },
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/17 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/122 Safari/537.36",
]

TOKENS_RESULTADO = {"GP", "NP"}


def limpiar_linea(valor: str) -> str:
    return " ".join(str(valor).replace("\xa0", " ").strip().split())


def normalizar_equipo(texto: str) -> str:
    texto = limpiar_linea(texto)
    texto = texto.replace("“", '"').replace("”", '"').replace("''", "''")
    texto = texto.replace(" .", ".")
    return texto.rstrip("-–:").strip()


def clave(texto: str) -> str:
    texto = normalizar_equipo(texto).upper()
    reemplazos = str.maketrans("ÁÉÍÓÚÜáéíóúü", "AEIOUUAEIOUU")
    texto = texto.translate(reemplazos)
    texto = texto.replace('"', "").replace("'", "")
    return re.sub(r"[^A-Z0-9Ñ]", "", texto)


def normalizar_categoria(texto: str) -> str:
    texto = limpiar_linea(texto).replace(" ", "")
    mapa = {
        "19": "2019", "13": "2013", "18": "2018", "14": "2014", "17": "2017", "16": "2016", "15": "2015",
        "2014/15": "2014/15", "2016/17": "2016/17", "2018/19": "2018/19",
        "2020/21/22": "2020/21/22", "2018/19/20": "2018/19/20",
    }
    return mapa.get(texto, limpiar_linea(texto))


def crear_scraper():
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
    }
    if cloudscraper is not None:
        scraper = cloudscraper.create_scraper()
        scraper.headers.update(headers)
        return scraper
    session = requests.Session()
    session.headers.update(headers)
    return session


def obtener_html(url: str, reintentos: int = 4, pausa: int = 4) -> str:
    ultimo_error = None
    for intento in range(1, reintentos + 1):
        try:
            print(f"Descargando {url} (intento {intento}/{reintentos})")
            scraper = crear_scraper()
            time.sleep(random.uniform(0.6, 1.4))
            r = scraper.get(url, timeout=60)
            r.raise_for_status()
            return r.text
        except Exception as error:
            ultimo_error = error
            print(f"Error descargando {url}: {error}")
            if intento < reintentos:
                time.sleep(pausa)
    raise ultimo_error


def obtener_lineas_desde_html(html: str) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    texto = soup.get_text("\n")
    return [limpiar_linea(x) for x in texto.splitlines() if limpiar_linea(x)]


def buscar_indice(lineas: List[str], predicado) -> int:
    for i, linea in enumerate(lineas):
        if predicado(linea):
            return i
    return -1


def partir_cruce(linea: str) -> Optional[Tuple[str, str]]:
    texto = normalizar_equipo(linea)
    partes = re.split(r"\s*vs\s*", texto, maxsplit=1, flags=re.I)
    if len(partes) != 2:
        return None
    local = normalizar_equipo(partes[0])
    visitante = normalizar_equipo(partes[1])
    if not local or not visitante:
        return None
    return local, visitante


def extraer_equipos_fixture(lineas: List[str]) -> List[str]:
    equipos = []
    for linea in lineas:
        cruce = partir_cruce(linea)
        if cruce:
            equipos.extend(cruce)
    return sorted({normalizar_equipo(e) for e in equipos if e}, key=len, reverse=True)


def encontrar_equipo_en_inicio(texto: str, equipos_ordenados: List[str]) -> Tuple[Optional[str], str]:
    texto_limpio = normalizar_equipo(texto)
    texto_clave = clave(texto_limpio)
    for equipo in equipos_ordenados:
        eq_clave = clave(equipo)
        if texto_clave.startswith(eq_clave):
            # Si está pegado al número, igual cortamos por el largo visible del nombre cuando coincide.
            if texto_limpio.upper().startswith(equipo.upper()):
                return equipo, texto_limpio[len(equipo):].strip()
            # Fallback para casos raros con acentos/comillas.
            m = re.search(r"(?:GP|NP|\d+)\b", texto_limpio, flags=re.I)
            return equipo, texto_limpio[m.start():].strip() if m else ""
    return None, texto_limpio


def sacar_fixture(lineas: List[str], nombre_equipo: str) -> List[Dict]:
    # FEFI a veces muestra LOCAL y VISITANTE en dos líneas separadas.
    inicio = buscar_indice(lineas, lambda l: limpiar_linea(l).upper() == "LOCAL VISITANTE")
    if inicio == -1:
        for i in range(len(lineas) - 1):
            if lineas[i].upper() == "LOCAL" and lineas[i + 1].upper() == "VISITANTE":
                inicio = i + 1
                break
    if inicio == -1:
        return []

    equipo_buscado = clave(nombre_equipo)
    fecha_actual = ""
    partidos: List[Dict] = []

    for linea in lineas[inicio + 1:]:
        texto = limpiar_linea(linea)
        upper = texto.upper()
        if upper.startswith("NO SE HA ENCONTRADO") or upper.startswith("NOMBRE DEL EQUIPO") or upper.startswith("F.T.EQUIPOS"):
            break
        if re.match(r"^Fecha\s+\d+", texto, flags=re.I):
            fecha_actual = texto
            continue
        cruce = partir_cruce(texto)
        if not cruce:
            continue
        local, visitante = cruce
        if equipo_buscado == clave(local) or equipo_buscado == clave(visitante):
            condicion = "Local" if equipo_buscado == clave(local) else "Visitante"
            m = re.search(r"Fecha\s+(\d+)", fecha_actual, flags=re.I)
            fecha_id = f"F{m.group(1)}" if m else ""
            partidos.append({
                "fecha": fecha_actual,
                "fecha_id": fecha_id,
                "local": local,
                "visitante": visitante,
                "condicion": condicion,
            })

    vistos = set()
    unicos = []
    for p in partidos:
        k = (p.get("fecha_id"), p.get("local"), p.get("visitante"))
        if k not in vistos:
            vistos.add(k)
            unicos.append(p)
    return unicos


def construir_diccionario_fechas(fixture: List[Dict]) -> Dict[str, Dict]:
    return {p.get("fecha_id", ""): p for p in fixture if p.get("fecha_id")}


def es_token_resultado(token: str) -> bool:
    t = token.strip().upper()
    return t in TOKENS_RESULTADO or t.isdigit()


def valor_resultado(token: str):
    token = token.strip().upper()
    return token if token else None


def parsear_fila_resultados(linea: str, equipos_ordenados: List[str], cantidad_categorias: int) -> Optional[Dict]:
    texto = normalizar_equipo(linea)
    fecha_id = None
    m = re.match(r"^(F\d+)\s*(.*)$", texto, flags=re.I)
    if m:
        fecha_id = m.group(1).upper()
        texto = limpiar_linea(m.group(2))

    texto = re.sub(r"\s+(Previo|Verificado)$", "", texto, flags=re.I).strip()
    equipo, resto = encontrar_equipo_en_inicio(texto, equipos_ordenados)
    if not equipo:
        return None

    tokens = re.findall(r"GP|NP|\d+", resto, flags=re.I)
    tokens = [t.upper() if t.upper() in TOKENS_RESULTADO else t for t in tokens]

    pj = None
    pts = None
    valores_categoria = [None] * cantidad_categorias

    if len(tokens) >= cantidad_categorias + 2:
        cat = tokens[:cantidad_categorias]
        pj_pts = tokens[cantidad_categorias:cantidad_categorias + 2]
        if all(es_token_resultado(t) for t in cat) and all(t.isdigit() for t in pj_pts):
            valores_categoria = [valor_resultado(t) for t in cat]
            pj = int(pj_pts[0])
            pts = int(pj_pts[1])
    elif len(tokens) >= 2 and tokens[0].isdigit() and tokens[1].isdigit():
        pj = int(tokens[0])
        pts = int(tokens[1])

    return {"fecha_id": fecha_id, "equipo": equipo, "pj": pj, "pts": pts, "categorias": valores_categoria}


def sacar_resultados(lineas: List[str], fixture: List[Dict], nombre_equipo: str, categorias: List[str], equipos_ordenados: List[str]) -> Dict:
    inicio = buscar_indice(lineas, lambda l: limpiar_linea(l).upper().startswith("F.T.EQUIPOS"))
    fin = buscar_indice(lineas[inicio + 1:] if inicio != -1 else [], lambda l: limpiar_linea(l).upper().startswith("EQUIPOS PJ"))
    if inicio == -1:
        return {"general": {}}
    fin_abs = inicio + 1 + fin if fin != -1 else len(lineas)
    bloque = lineas[inicio + 1:fin_abs]

    fechas_fixture = construir_diccionario_fechas(fixture)
    equipo_buscado = clave(nombre_equipo)
    general: Dict[str, List[Dict]] = {}
    i = 0

    while i < len(bloque) - 1:
        fila_local = parsear_fila_resultados(bloque[i], equipos_ordenados, len(categorias))
        fila_visitante = parsear_fila_resultados(bloque[i + 1], equipos_ordenados, len(categorias))

        if not fila_local or not fila_visitante or not fila_local.get("fecha_id"):
            i += 1
            continue

        local = fila_local["equipo"]
        visitante = fila_visitante["equipo"]
        if equipo_buscado != clave(local) and equipo_buscado != clave(visitante):
            i += 2
            continue

        fecha_id = fila_local["fecha_id"]
        resultados_categoria = {}
        for idx, categoria in enumerate(categorias):
            resultados_categoria[categoria] = {
                "local": fila_local["categorias"][idx] if idx < len(fila_local["categorias"]) else None,
                "visitante": fila_visitante["categorias"][idx] if idx < len(fila_visitante["categorias"]) else None,
            }

        general.setdefault(fecha_id, []).append({
            "fecha_id": fecha_id,
            "fecha": fechas_fixture.get(fecha_id, {}).get("fecha", fecha_id),
            "local": local,
            "visitante": visitante,
            "pj_local": fila_local.get("pj"),
            "pts_local": fila_local.get("pts"),
            "pj_visitante": fila_visitante.get("pj"),
            "pts_visitante": fila_visitante.get("pts"),
            "resultados": resultados_categoria,
        })
        i += 2

    return {"general": general}


def parsear_fila_tabla(linea: str, equipos_ordenados: List[str]) -> Optional[Dict]:
    texto = normalizar_equipo(linea)
    equipo, resto = encontrar_equipo_en_inicio(texto, equipos_ordenados)
    if not equipo:
        return None
    nums = re.findall(r"\d+", resto)
    if len(nums) < 5:
        return None
    pj, g, e, p, pts = map(int, nums[:5])
    return {"equipo": equipo, "pj": pj, "g": g, "e": e, "p": p, "pts": pts}


def sacar_tablas(lineas: List[str], categorias: List[str], equipos_ordenados: List[str]) -> Dict:
    inicio = buscar_indice(lineas, lambda l: limpiar_linea(l).upper().startswith("EQUIPOS PJ"))
    if inicio == -1:
        return {"general": [], "categorias": {c: [] for c in categorias}}

    resultado = {"general": [], "categorias": {c: [] for c in categorias}}
    seccion_actual: Optional[str] = None
    categorias_set = set(categorias)

    for linea in lineas[inicio + 1:]:
        texto = limpiar_linea(linea)
        upper = texto.upper()
        if not texto:
            continue
        if upper.startswith("RESULTADOS") or upper.startswith("TABLAS") or upper.startswith("FIXTURE"):
            continue
        if upper.startswith("©") or upper.startswith("SUSCRIBITE") or upper.startswith("TORNEOS"):
            break

        cat = normalizar_categoria(texto)
        if upper == "GENERAL":
            seccion_actual = "general"
            continue
        if cat in categorias_set:
            seccion_actual = cat
            resultado["categorias"].setdefault(cat, [])
            continue

        fila = parsear_fila_tabla(texto, equipos_ordenados)
        if not fila or not seccion_actual:
            continue
        if seccion_actual == "general":
            resultado["general"].append(fila)
        else:
            resultado["categorias"].setdefault(seccion_actual, []).append(fila)

    return resultado


def sacar_direcciones(lineas: List[str], equipos_ordenados: List[str]) -> Dict[str, str]:
    inicio = buscar_indice(lineas, lambda l: limpiar_linea(l).upper().startswith("NOMBRE DEL EQUIPO DIRECCI"))
    if inicio == -1:
        return {}
    fin = buscar_indice(lineas[inicio + 1:], lambda l: limpiar_linea(l).upper().startswith("F.T.EQUIPOS"))
    fin_abs = inicio + 1 + fin if fin != -1 else len(lineas)
    bloque = lineas[inicio + 1:fin_abs]

    direcciones: Dict[str, str] = {}
    for linea in bloque:
        texto = limpiar_linea(linea)
        equipo, resto = encontrar_equipo_en_inicio(texto, equipos_ordenados)
        if not equipo:
            continue
        direccion = re.sub(r"\s+(SI|NO)$", "", resto, flags=re.I).strip()
        if direccion:
            direcciones[equipo] = direccion
    return direcciones


def guardar_json(path: str, data) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def cargar_json_si_existe(path: str, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def procesar_zona(zona: str, cfg: Dict, actualizar: bool) -> None:
    carpeta = os.path.join("data", zona)
    os.makedirs(carpeta, exist_ok=True)

    fixture_path = os.path.join(carpeta, "fixture.json")
    tabla_path = os.path.join(carpeta, "tabla.json")
    resultados_path = os.path.join(carpeta, "resultados.json")
    direcciones_path = os.path.join(carpeta, "direcciones.json")

    if not actualizar:
        fixture = cargar_json_si_existe(fixture_path, [])
        tabla = cargar_json_si_existe(tabla_path, {"general": [], "categorias": {}})
        resultados = cargar_json_si_existe(resultados_path, {"general": {}})
        direcciones = cargar_json_si_existe(direcciones_path, {})
        print(f"Zona {zona}: fixture={len(fixture)} | tabla_general={len(tabla.get('general', []))} | resultados={len(resultados.get('general', {}))} | direcciones={len(direcciones)}")
        return

    print(f"Actualizando {zona}: {cfg['url']}")
    html = obtener_html(cfg["url"])
    lineas = obtener_lineas_desde_html(html)

    equipos = extraer_equipos_fixture(lineas)
    if cfg["equipo"] not in equipos:
        equipos.append(cfg["equipo"])
    equipos = sorted({normalizar_equipo(e) for e in equipos if e}, key=len, reverse=True)

    fixture_nuevo = sacar_fixture(lineas, cfg["equipo"])
    if fixture_nuevo:
        guardar_json(fixture_path, fixture_nuevo)
        fixture = fixture_nuevo
    else:
        fixture = cargar_json_si_existe(fixture_path, [])

    tabla = sacar_tablas(lineas, cfg["categorias"], equipos)
    resultados = sacar_resultados(lineas, fixture, cfg["equipo"], cfg["categorias"], equipos)
    direcciones = sacar_direcciones(lineas, equipos)

    guardar_json(tabla_path, tabla)
    guardar_json(resultados_path, resultados)
    guardar_json(direcciones_path, direcciones)

    print(
        f"Zona {zona}: fixture={len(fixture)} | "
        f"tabla_general={len(tabla.get('general', []))} | "
        f"resultados={len(resultados.get('general', {}))} | "
        f"direcciones={len(direcciones)}"
    )

    if len(tabla.get("general", [])) == 0:
        print("  AVISO: no encontró tabla general. Primeras líneas útiles alrededor de EQUIPOS PJ:")
        idx = buscar_indice(lineas, lambda l: limpiar_linea(l).upper().startswith("EQUIPOS PJ"))
        for l in lineas[max(0, idx): idx + 12] if idx != -1 else lineas[:12]:
            print("   -", l)


def main() -> None:
    actualizar = len(sys.argv) > 1 and sys.argv[1].lower() in {"actualizar", "update", "descargar"}

    if not actualizar:
        print("LISTO. No se conectó a FEFI. Para actualizar tablas/resultados manualmente: python scraper.py actualizar")

    for zona, cfg in ZONAS.items():
        procesar_zona(zona, cfg, actualizar)

    if actualizar:
        print("\nLISTO. Se descargó UNA VEZ desde FEFI y quedó guardado en data/<zona>.")
        print("Ahora hacé: git add .  |  git commit -m \"actualizar tablas y resultados\"  |  git push")


if __name__ == "__main__":
    main()
