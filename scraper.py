
import json
import os
import random
import re
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
        "categorias_resultados": ["2019", "2013", "2018", "2014", "2017", "2016", "2015"],
        "categorias_tablas": ["2019", "2013", "2018", "2014", "2017", "2016", "2015"],
    },
    "i": {
        "url": "https://fefi.com.ar/2026-torneo-anual-baby-futbol/i/",
        "equipo": 'ALL BOYS "B"',
        "categorias_resultados": ["2019", "2013", "2018", "2014", "2017", "2016", "2015"],
        "categorias_tablas": ["2019", "2013", "2018", "2014", "2017", "2016", "2015"],
    },
    "mat1": {
        "url": "https://fefi.com.ar/2026-torneo-anual-baby-futbol/mat-1/",
        "equipo": "LOS ALBOS",
        "categorias_resultados": ["2013", "2014/15", "2016/17", "2018/19", "2020/21/22"],
        "categorias_tablas": ["2013", "2014/15", "2016/17", "2018/19", "2020/21/22"],
    },
    "mat4": {
        "url": "https://fefi.com.ar/2026-torneo-anual-baby-futbol/mat-4/",
        "equipo": "ALL BOYS",
        "categorias_resultados": ["2013", "2014", "2015", "2016", "2017", "2018/19/20"],
        "categorias_tablas": ["2013", "2014", "2015", "2016", "2017", "2018/19/20"],
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


def normalizar_categoria(texto: str) -> str:
    texto = limpiar_linea(texto)
    reemplazos = {
        "19": "2019",
        "13": "2013",
        "18": "2018",
        "14": "2014",
        "17": "2017",
        "16": "2016",
        "15": "2015",
        "2014 / 15": "2014/15",
        "2016 / 17": "2016/17",
        "2018 / 19": "2018/19",
        "2018/19/20": "2018/19/20",
        "2020 / 21 / 22": "2020/21/22",
    }
    return reemplazos.get(texto, texto)


def normalizar_equipo(texto: str) -> str:
    return limpiar_linea(texto).rstrip("-–:")


def crear_scraper():
    if cloudscraper is not None:
        scraper = cloudscraper.create_scraper()
        scraper.headers.update({"User-Agent": random.choice(USER_AGENTS)})
        return scraper
    session = requests.Session()
    session.headers.update({"User-Agent": random.choice(USER_AGENTS)})
    return session


def obtener_html(url: str, reintentos: int = 4, pausa: int = 5) -> str:
    ultimo_error = None
    for intento in range(1, reintentos + 1):
        try:
            print(f"Descargando {url} (intento {intento}/{reintentos})")
            scraper = crear_scraper()
            time.sleep(random.uniform(1.5, 3.5))
            respuesta = scraper.get(url, timeout=60)
            respuesta.raise_for_status()
            return respuesta.text
        except Exception as error:
            ultimo_error = error
            print(f"Error descargando {url}: {error}")
            if intento < reintentos:
                time.sleep(pausa)
    raise ultimo_error


def obtener_lineas_desde_html(html: str) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    texto = soup.get_text("\n")
    return [limpiar_linea(linea) for linea in texto.splitlines() if limpiar_linea(linea)]


def indice_linea(lineas: List[str], texto_objetivo: str) -> int:
    objetivo = limpiar_linea(texto_objetivo).upper()
    for i, linea in enumerate(lineas):
        if limpiar_linea(linea).upper() == objetivo:
            return i
    return -1


def cortar_bloque(lineas: List[str], inicio_titulo: str, fin_titulos: List[str]) -> List[str]:
    inicio = indice_linea(lineas, inicio_titulo)
    if inicio == -1:
        return []
    fin_titulos_normalizados = {limpiar_linea(x).upper() for x in fin_titulos}
    bloque = []
    for linea in lineas[inicio + 1:]:
        if limpiar_linea(linea).upper() in fin_titulos_normalizados:
            break
        bloque.append(linea)
    return bloque


def partir_cruce(linea: str) -> Optional[Tuple[str, str]]:
    texto = limpiar_linea(linea)
    match = re.match(r"^(.*?)\s*vs\s*(.*?)$", texto, flags=re.IGNORECASE)
    if not match:
        return None
    local = normalizar_equipo(match.group(1))
    visitante = normalizar_equipo(match.group(2))
    if not local or not visitante:
        return None
    return local, visitante


def sacar_fixture(lineas: List[str], nombre_equipo: str) -> List[Dict]:
    bloque = cortar_bloque(
        lineas,
        "FIXTURE APERTURA",
        [
            "FIXTURE CLAUSURA",
            "DIRECCIONES",
            "RESULTADOS APERTURA",
            "TABLAS APERTURA",
            "RESULTADOS CLAUSURA",
            "TABLAS CLAUSURA",
            "TABLAS ANUALES",
            "NO SE HA ENCONTRADO CONTENIDO",
        ],
    )
    if not bloque:
        bloque = lineas

    equipo_buscado = nombre_equipo.upper()
    fecha_actual = ""
    partidos = []

    i = 0
    while i < len(bloque):
        texto = limpiar_linea(bloque[i])

        if texto.startswith("Fecha"):
            fecha_actual = texto
            i += 1
            continue

        cruce = partir_cruce(texto)
        if cruce:
            local, visitante = cruce
            if equipo_buscado in local.upper() or equipo_buscado in visitante.upper():
                condicion = "Local" if equipo_buscado in local.upper() else "Visitante"
                match_fecha = re.search(r"Fecha\s+(\d+)", fecha_actual, re.I)
                fecha_id = f"F{match_fecha.group(1)}" if match_fecha else ""
                partidos.append(
                    {
                        "fecha": fecha_actual,
                        "fecha_id": fecha_id,
                        "local": local,
                        "visitante": visitante,
                        "condicion": condicion,
                    }
                )
        i += 1

    vistos = set()
    unicos = []
    for partido in partidos:
        clave = (partido["fecha"], partido["local"], partido["visitante"], partido["condicion"])
        if clave not in vistos:
            vistos.add(clave)
            unicos.append(partido)
    return unicos


def construir_diccionario_fechas(fixture: List[Dict]) -> Dict[str, Dict]:
    por_fecha = {}
    for item in fixture:
        por_fecha[item["fecha_id"]] = item
    return por_fecha


def extraer_todos_los_equipos(lineas: List[str]) -> List[str]:
    equipos = []
    for linea in lineas:
        cruce = partir_cruce(linea)
        if cruce:
            equipos.extend(cruce)
    return sorted({normalizar_equipo(x) for x in equipos if x}, key=len, reverse=True)


def encontrar_equipo_en_inicio(texto: str, equipos_ordenados: List[str]) -> Tuple[Optional[str], str]:
    texto_limpio = limpiar_linea(texto)
    texto_upper = texto_limpio.upper()
    for equipo in equipos_ordenados:
        equipo_norm = normalizar_equipo(equipo)
        if texto_upper.startswith(equipo_norm.upper()):
            resto = texto_limpio[len(equipo_norm):].strip()
            return equipo_norm, resto
    return None, texto_limpio


def es_token_resultado(token: str) -> bool:
    token = token.strip().upper()
    return token in TOKENS_RESULTADO or token.isdigit()


def valor_resultado(token: str):
    token = token.strip()
    if token == "":
        return None
    return token


def parsear_fila_resultados(linea: str, equipos_ordenados: List[str], cantidad_categorias: int) -> Optional[Dict]:
    texto = limpiar_linea(linea)
    fecha_id = None

    match_fecha = re.match(r"^(F\d+)\s*(.*)$", texto, flags=re.I)
    if match_fecha:
        fecha_id = match_fecha.group(1).upper()
        texto = limpiar_linea(match_fecha.group(2))

    texto = re.sub(r"\s+Previo$", "", texto, flags=re.I)
    equipo, resto = encontrar_equipo_en_inicio(texto, equipos_ordenados)
    if not equipo:
        return None

    tokens = resto.split()
    pj = None
    pts = None
    valores_categoria = [None] * cantidad_categorias

    if len(tokens) >= cantidad_categorias + 2 and all(es_token_resultado(t) for t in tokens[:cantidad_categorias]) and all(t.isdigit() for t in tokens[cantidad_categorias:cantidad_categorias+2]):
        valores_categoria = [valor_resultado(t) for t in tokens[:cantidad_categorias]]
        pj = int(tokens[cantidad_categorias])
        pts = int(tokens[cantidad_categorias + 1])
    elif len(tokens) >= 2 and all(t.isdigit() for t in tokens[:2]):
        pj = int(tokens[0])
        pts = int(tokens[1])

    return {
        "fecha_id": fecha_id,
        "equipo": equipo,
        "pj": pj,
        "pts": pts,
        "categorias": valores_categoria,
    }


def sacar_resultados(lineas: List[str], fixture: List[Dict], nombre_equipo: str, categorias: List[str]) -> Dict:
    equipos_ordenados = extraer_todos_los_equipos(lineas)
    fechas_fixture = construir_diccionario_fechas(fixture)

    inicio = next((i for i, l in enumerate(lineas) if limpiar_linea(l).upper().startswith("F.T.EQUIPOS")), -1)
    fin = indice_linea(lineas, "EQUIPOS PJ G E P Pts.")
    if inicio == -1 or fin == -1 or fin <= inicio:
        return {"general": {}}

    bloque = lineas[inicio + 1:fin]
    general: Dict[str, List[Dict]] = {}
    i = 0
    equipo_buscado = nombre_equipo.upper()

    while i < len(bloque) - 1:
        fila_local = parsear_fila_resultados(bloque[i], equipos_ordenados, len(categorias))
        fila_visitante = parsear_fila_resultados(bloque[i + 1], equipos_ordenados, len(categorias))

        if not fila_local or not fila_visitante or not fila_local.get("fecha_id"):
            i += 1
            continue

        fecha_id = fila_local["fecha_id"]
        local = fila_local["equipo"]
        visitante = fila_visitante["equipo"]

        if equipo_buscado not in local.upper() and equipo_buscado not in visitante.upper():
            i += 2
            continue

        resultados_categoria = {}
        for idx, categoria in enumerate(categorias):
            resultados_categoria[categoria] = {
                "local": fila_local["categorias"][idx] if idx < len(fila_local["categorias"]) else None,
                "visitante": fila_visitante["categorias"][idx] if idx < len(fila_visitante["categorias"]) else None,
            }

        partido = {
            "fecha_id": fecha_id,
            "fecha": fechas_fixture.get(fecha_id, {}).get("fecha", fecha_id),
            "local": local,
            "visitante": visitante,
            "pj_local": fila_local.get("pj"),
            "pts_local": fila_local.get("pts"),
            "pj_visitante": fila_visitante.get("pj"),
            "pts_visitante": fila_visitante.get("pts"),
            "resultados": resultados_categoria,
        }
        general.setdefault(fecha_id, []).append(partido)
        i += 2

    return {"general": general}


def parsear_fila_tabla(linea: str, equipos_ordenados: List[str]) -> Optional[Dict]:
    texto = limpiar_linea(linea)
    equipo, resto = encontrar_equipo_en_inicio(texto, equipos_ordenados)
    if not equipo:
        return None

    tokens = resto.split()
    if len(tokens) < 5:
        return None
    if not all(token.isdigit() for token in tokens[:5]):
        return None

    pj, g, e, p, pts = map(int, tokens[:5])
    return {"equipo": equipo, "pj": pj, "g": g, "e": e, "p": p, "pts": pts}


def sacar_tablas(lineas: List[str], categorias_tablas: List[str]) -> Dict:
    equipos_ordenados = extraer_todos_los_equipos(lineas)
    inicio = indice_linea(lineas, "EQUIPOS PJ G E P Pts.")
    if inicio == -1:
        return {"general": [], "categorias": {}}

    resultado = {"general": [], "categorias": {}}
    seccion_actual = None

    for linea in lineas[inicio + 1:]:
        texto = limpiar_linea(linea)

        if texto.upper() in {
            "NO SE HA ENCONTRADO CONTENIDO",
            "NOMBRE DEL EQUIPO DIRECCIÓN LOCALIDAD T.",
            "NOMBRE DEL EQUIPO DIRECCION LOCALIDAD T.",
        }:
            break

        texto_cat = normalizar_categoria(texto)
        if texto.upper() == "GENERAL":
            seccion_actual = "general"
            continue

        if texto_cat in categorias_tablas:
            seccion_actual = texto_cat
            resultado["categorias"].setdefault(seccion_actual, [])
            continue

        fila = parsear_fila_tabla(texto, equipos_ordenados)
        if not fila or not seccion_actual:
            continue

        if seccion_actual == "general":
            resultado["general"].append(fila)
        else:
            resultado["categorias"][seccion_actual].append(fila)

    return resultado


def guardar_json(clave: str, nombre_archivo: str, data):
    os.makedirs(os.path.join("data", clave), exist_ok=True)

    ruta_data = os.path.join("data", clave, f"{nombre_archivo}.json")
    with open(ruta_data, "w", encoding="utf-8") as archivo:
        json.dump(data, archivo, ensure_ascii=False, indent=2)

    ruta_plana = f"{nombre_archivo}_{clave}.json"
    with open(ruta_plana, "w", encoding="utf-8") as archivo:
        json.dump(data, archivo, ensure_ascii=False, indent=2)

    print(f"Creado: {ruta_data}")
    print(f"Creado: {ruta_plana}")


def procesar_zona(clave: str, info: Dict):
    html = obtener_html(info["url"])
    lineas = obtener_lineas_desde_html(html)

    fixture = sacar_fixture(lineas, info["equipo"])
    tablas = sacar_tablas(lineas, info["categorias_tablas"])
    resultados = sacar_resultados(lineas, fixture, info["equipo"], info["categorias_resultados"])

    guardar_json(clave, "fixture", fixture)
    guardar_json(clave, "tabla", tablas)
    guardar_json(clave, "resultados", resultados)


def main():
    errores = []
    zonas_ok = 0

    for clave, info in ZONAS.items():
        print(f"Procesando {clave}...")
        try:
            procesar_zona(clave, info)
            zonas_ok += 1
        except Exception as error:
            mensaje = f"Falló zona {clave}: {error}"
            print(mensaje)
            errores.append(mensaje)

    if zonas_ok == 0:
        raise RuntimeError("No se pudo actualizar ninguna zona.")

    if errores:
        print("Hubo zonas con error:")
        for error in errores:
            print("-", error)


if __name__ == "__main__":
    main()
