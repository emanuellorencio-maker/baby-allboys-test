import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from bs4 import BeautifulSoup

ZONAS = {
    "c": {
        "url": "https://fefi.com.ar/2026-torneo-anual-baby-futbol/c/#botonera",
        "equipo": 'ALL BOYS "A"',
        "categorias": ["2019", "2013", "2018", "2014", "2017", "2016", "2015"],
    },
    "i": {
        "url": "https://fefi.com.ar/2026-torneo-anual-baby-futbol/i/#botonera",
        "equipo": 'ALL BOYS "B"',
        "categorias": ["2019", "2013", "2018", "2014", "2017", "2016", "2015"],
    },
    "mat1": {
        "url": "https://fefi.com.ar/2026-torneo-anual-baby-futbol/mat-1/#botonera",
        "equipo": "LOS ALBOS",
        "categorias": ["2013", "2014/15", "2016/17", "2018/19", "2020/21/22"],
    },
    "mat4": {
        "url": "https://fefi.com.ar/2026-torneo-anual-baby-futbol/mat-4/#botonera",
        "equipo": "ALL BOYS",
        "categorias": ["2013", "2014", "2015", "2016", "2017", "2018/19/20"],
    },
}

FIXTURES_FIJOS = {
  "c": [
    {"fecha":"Fecha 1 - 18 de Abril","fecha_id":"F1","local":"ALL BOYS \"A\"","visitante":"PUEYRREDON","condicion":"Local"},
    {"fecha":"Fecha 2 - 25 de Abril","fecha_id":"F2","local":"C. S. D. PARQUE","visitante":"ALL BOYS \"A\"","condicion":"Visitante"},
    {"fecha":"Fecha 3 - 02 de Mayo","fecha_id":"F3","local":"ALL BOYS \"A\"","visitante":"BICHOS COLORADOS","condicion":"Local"},
    {"fecha":"Fecha 4 - 09 de Mayo","fecha_id":"F4","local":"CLUB OESTE","visitante":"ALL BOYS \"A\"","condicion":"Visitante"},
    {"fecha":"Fecha 5 - 16 de Mayo","fecha_id":"F5","local":"ALL BOYS \"A\"","visitante":"DON BOSCO","condicion":"Local"},
    {"fecha":"Fecha 6 - 23 de Mayo","fecha_id":"F6","local":"CENTRO ESPAÑOL","visitante":"ALL BOYS \"A\"","condicion":"Visitante"},
    {"fecha":"Fecha 7 - 30 de Mayo","fecha_id":"F7","local":"ALL BOYS \"A\"","visitante":"U.D.S. ALLENDE","condicion":"Local"},
    {"fecha":"Fecha 8 - 06 de Junio","fecha_id":"F8","local":"RACING CLUB 1","visitante":"ALL BOYS \"A\"","condicion":"Visitante"},
    {"fecha":"Fecha 9 - 13 de Junio","fecha_id":"F9","local":"ALL BOYS \"A\"","visitante":"ESTRELLA DE MALDONADO ''B''","condicion":"Local"},
    {"fecha":"Fecha 10 - 20 de Junio","fecha_id":"F10","local":"LOS CAMBOYANOS","visitante":"ALL BOYS \"A\"","condicion":"Visitante"},
    {"fecha":"Fecha 11 - 27 de Junio","fecha_id":"F11","local":"ALL BOYS \"A\"","visitante":"INDEPENDIENTE DE HURLINGHAM","condicion":"Local"},
    {"fecha":"Fecha 12 - 04 de Julio","fecha_id":"F12","local":"ALL BOYS \"A\"","visitante":"MARIANO MORENO","condicion":"Local"},
    {"fecha":"Fecha 13 - 11 de Julio","fecha_id":"F13","local":"SANTIAGO DE LINIERS","visitante":"ALL BOYS \"A\"","condicion":"Visitante"},
    {"fecha":"Fecha 14 - 18 de Julio","fecha_id":"F14","local":"ALL BOYS \"A\"","visitante":"INDEPENDIENTE","condicion":"Local"},
    {"fecha":"Fecha 15 - 01 de Agosto","fecha_id":"F15","local":"D. F. SARMIENTO","visitante":"ALL BOYS \"A\"","condicion":"Visitante"}
  ],
  "i": [
    {"fecha":"Fecha 1 - 18 de Abril","fecha_id":"F1","local":"SOLDATI 32 F. C.","visitante":"ALL BOYS \"B\"","condicion":"Visitante"},
    {"fecha":"Fecha 2 - 25 de Abril","fecha_id":"F2","local":"ALL BOYS \"B\"","visitante":"CLUB CIENCIA Y LABOR","condicion":"Local"},
    {"fecha":"Fecha 3 - 02 de Mayo","fecha_id":"F3","local":"VILLA REAL ROJO","visitante":"ALL BOYS \"B\"","condicion":"Visitante"},
    {"fecha":"Fecha 4 - 09 de Mayo","fecha_id":"F4","local":"ALL BOYS \"B\"","visitante":"MARCHIGIANA","condicion":"Local"},
    {"fecha":"Fecha 5 - 16 de Mayo","fecha_id":"F5","local":"LUJAN DE LOS PATRIOTAS","visitante":"ALL BOYS \"B\"","condicion":"Visitante"},
    {"fecha":"Fecha 6 - 23 de Mayo","fecha_id":"F6","local":"ALL BOYS \"B\"","visitante":"LA MARCA","condicion":"Local"},
    {"fecha":"Fecha 7 - 30 de Mayo","fecha_id":"F7","local":"LUGANO TENNIS CLUB","visitante":"ALL BOYS \"B\"","condicion":"Visitante"},
    {"fecha":"Fecha 8 - 06 de Junio","fecha_id":"F8","local":"ALL BOYS \"B\"","visitante":"EL TREBOL F. C.","condicion":"Local"},
    {"fecha":"Fecha 9 - 13 de Junio","fecha_id":"F9","local":"LOS ANDES","visitante":"ALL BOYS \"B\"","condicion":"Visitante"},
    {"fecha":"Fecha 10 - 20 de Junio","fecha_id":"F10","local":"ALL BOYS \"B\"","visitante":"AÑASCO","condicion":"Local"},
    {"fecha":"Fecha 11 - 27 de Junio","fecha_id":"F11","local":"LIGA FOMENTO VILLA MITRE","visitante":"ALL BOYS \"B\"","condicion":"Visitante"},
    {"fecha":"Fecha 12 - 04 de Julio","fecha_id":"F12","local":"K. A. C.","visitante":"ALL BOYS \"B\"","condicion":"Visitante"},
    {"fecha":"Fecha 13 - 11 de Julio","fecha_id":"F13","local":"ALL BOYS \"B\"","visitante":"HURACAN","condicion":"Local"},
    {"fecha":"Fecha 14 - 18 de Julio","fecha_id":"F14","local":"LOMAS BLANCO","visitante":"ALL BOYS \"B\"","condicion":"Visitante"},
    {"fecha":"Fecha 15 - 01 de Agosto","fecha_id":"F15","local":"ALL BOYS \"B\"","visitante":"FATIMA","condicion":"Local"}
  ],
  "mat1": [
    {"fecha":"Fecha 1 - 18 de Abril","fecha_id":"F1","local":"LOS ALBOS","visitante":"LOS CUERVOS","condicion":"Local"},
    {"fecha":"Fecha 2 - 25 de ABril","fecha_id":"F2","local":"NUEVA CHICAGO","visitante":"LOS ALBOS","condicion":"Visitante"},
    {"fecha":"Fecha 3 - 02 de Mayo","fecha_id":"F3","local":"LOS ALBOS","visitante":"SANELI F.C.","condicion":"Local"},
    {"fecha":"Fecha 4 - 09 de Mayo","fecha_id":"F4","local":"CLUB PACIFICO","visitante":"LOS ALBOS","condicion":"Visitante"},
    {"fecha":"Fecha 5 - 16 de Mayo","fecha_id":"F5","local":"LOS ALBOS","visitante":"CLUB AT. LUGANO","condicion":"Local"},
    {"fecha":"Fecha 6 - 23 de Mayo","fecha_id":"F6","local":"VILLA LURO NORTE","visitante":"LOS ALBOS","condicion":"Visitante"},
    {"fecha":"Fecha 7 - 30 de Mayo","fecha_id":"F7","local":"LOS ALBOS","visitante":"FLORES CLUB","condicion":"Local"},
    {"fecha":"Fecha 8 - 06 de Junio","fecha_id":"F8","local":"LOS ALBOS","visitante":"VILLA HERMINIA","condicion":"Local"},
    {"fecha":"Fecha 9 - 13 de Junio","fecha_id":"F9","local":"PLATENSE BLANCO","visitante":"LOS ALBOS","condicion":"Visitante"},
    {"fecha":"Fecha 10 - 20 de Junio","fecha_id":"F10","local":"LOS ALBOS","visitante":"A. A. A. J.","condicion":"Local"},
    {"fecha":"Fecha 11 - 27 de Junio","fecha_id":"F11","local":"C. A. VIRGEN DEL CARMEN","visitante":"LOS ALBOS","condicion":"Visitante"},
    {"fecha":"Fecha 12 - 04 de Julio","fecha_id":"F12","local":"LOS ALBOS","visitante":"EST. PORTEÑO ROJO","condicion":"Local"},
    {"fecha":"Fecha 13 - 11 de Julio","fecha_id":"F13","local":"C. S. y D. PAMPERO","visitante":"LOS ALBOS","condicion":"Visitante"},
    {"fecha":"Fecha 14 - 18 de Julio","fecha_id":"F14","local":"LOS ALBOS","visitante":"ESTRELLA DE BOEDO","condicion":"Local"},
    {"fecha":"Fecha 15 - 01 de Agosto","fecha_id":"F15","local":"CLUB LA PATERNAL","visitante":"LOS ALBOS","condicion":"Visitante"}
  ],
  "mat4": [
    {"fecha":"Fecha 1 - 18 de Abril","fecha_id":"F1","local":"LOS CARASUCIAS","visitante":"ALL BOYS","condicion":"Visitante"},
    {"fecha":"Fecha 2 - 25 de ABril","fecha_id":"F2","local":"ALL BOYS","visitante":"ALMAFUERTE FUTBOL CLUB","condicion":"Local"},
    {"fecha":"Fecha 3 - 02 de Mayo","fecha_id":"F3","local":"EROS","visitante":"ALL BOYS","condicion":"Visitante"},
    {"fecha":"Fecha 4 - 09 de Mayo","fecha_id":"F4","local":"ALL BOYS","visitante":"ALVEAR","condicion":"Local"},
    {"fecha":"Fecha 5 - 16 de Mayo","fecha_id":"F5","local":"C. A. ATLANTA","visitante":"ALL BOYS","condicion":"Visitante"},
    {"fecha":"Fecha 6 - 23 de Mayo","fecha_id":"F6","local":"ALL BOYS","visitante":"C. A. VERSAILLES BLANCO","condicion":"Local"},
    {"fecha":"Fecha 7 - 30 de Mayo","fecha_id":"F7","local":"V. L. N.","visitante":"ALL BOYS","condicion":"Visitante"},
    {"fecha":"Fecha 8 - 06 de Junio","fecha_id":"F8","local":"CE. F. F. LA INDEPENDENCIA","visitante":"ALL BOYS","condicion":"Visitante"},
    {"fecha":"Fecha 9 - 13 de Junio","fecha_id":"F9","local":"ALL BOYS","visitante":"COMPLEJO COSTAS CELESTE","condicion":"Local"},
    {"fecha":"Fecha 10 - 20 de Junio","fecha_id":"F10","local":"PARQUE PATRICIOS","visitante":"ALL BOYS","condicion":"Visitante"},
    {"fecha":"Fecha 11 - 27 de Junio","fecha_id":"F11","local":"ALL BOYS","visitante":"EL TIFON DE BOYACA","condicion":"Local"},
    {"fecha":"Fecha 12 - 04 de Julio","fecha_id":"F12","local":"CICLON FORTIN","visitante":"ALL BOYS","condicion":"Visitante"},
    {"fecha":"Fecha 13 - 11 de Julio","fecha_id":"F13","local":"ALL BOYS","visitante":"SP. PEREYRA","condicion":"Local"},
    {"fecha":"Fecha 14 - 18 de Julio","fecha_id":"F14","local":"HURACAN TIKI TIKI","visitante":"ALL BOYS","condicion":"Visitante"},
    {"fecha":"Fecha 15 - 01 de Agosto","fecha_id":"F15","local":"ALL BOYS","visitante":"C. A. ESTUDIANTES","condicion":"Local"}
  ]
}

DIRECCIONES_FIJAS = {z: {} for z in ZONAS}


def normalizar(valor: str) -> str:
    return " ".join(str(valor or "").replace("\xa0", " ").strip().split())


def canon(valor: str) -> str:
    texto = normalizar(valor).upper().replace('"', '').replace("'", "")
    for a, b in [("Á","A"),("É","E"),("Í","I"),("Ó","O"),("Ú","U")]:
        texto = texto.replace(a,b)
    return re.sub(r"[^A-Z0-9Ñ]", "", texto)


def guardar_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def leer_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def asegurar_fixture_y_archivos_base():
    for zona, fixture in FIXTURES_FIJOS.items():
        base = Path("data") / zona
        base.mkdir(parents=True, exist_ok=True)
        guardar_json(base / "fixture.json", fixture)
        if not (base / "tabla.json").exists():
            guardar_json(base / "tabla.json", {"general": [], "categorias": {c: [] for c in ZONAS[zona]["categorias"]}})
        if not (base / "resultados.json").exists():
            guardar_json(base / "resultados.json", {"general": {}, "categorias": {}})
        if not (base / "direcciones.json").exists():
            guardar_json(base / "direcciones.json", DIRECCIONES_FIJAS.get(zona, {}))


def obtener_htmls_renderizados(url: str) -> List[str]:
    """Abre FEFI como Chrome real, captura la tabla inicial y después
    entra a RESULTADOS APERTURA para recorrer todas las páginas de la tabla.
    """
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        print("ERROR: falta Playwright.")
        print("Ejecutá una sola vez:")
        print("  pip install playwright")
        print("  python -m playwright install chromium")
        raise SystemExit(1)

    def click_siguiente_visible(page) -> bool:
        js = """
        () => {
          const visible = (el) => {
            const st = window.getComputedStyle(el);
            const r = el.getBoundingClientRect();
            return st.display !== 'none' && st.visibility !== 'hidden' && r.width > 0 && r.height > 0;
          };
          const candidatos = Array.from(document.querySelectorAll('a, button, span'));
          for (const el of candidatos) {
            const txt = (el.textContent || '').trim().toLowerCase();
            const cls = (el.className || '').toString().toLowerCase();
            const aria = (el.getAttribute('aria-label') || '').toLowerCase();
            const esNext = txt === 'next' || txt === 'siguiente' || txt === '>' || txt === '›' || txt === '»' || cls.includes('next') || aria.includes('next') || aria.includes('siguiente');
            const disabled = cls.includes('disabled') || el.getAttribute('aria-disabled') === 'true' || el.disabled;
            if (esNext && !disabled && visible(el)) { el.click(); return true; }
          }
          return false;
        }
        """
        try:
            return bool(page.evaluate(js))
        except Exception:
            return False

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1700, "height": 1300})
        page.goto(url, wait_until="networkidle", timeout=90000)
        try:
            page.wait_for_selector("table", timeout=25000)
        except Exception:
            pass
        time.sleep(2)

        htmls = [page.content()]

        try:
            page.get_by_text("RESULTADOS APERTURA", exact=False).first.click(timeout=7000)
            page.wait_for_timeout(1500)
        except Exception:
            try:
                page.locator("text=RESULTADOS").first.click(timeout=7000)
                page.wait_for_timeout(1500)
            except Exception:
                pass

        vistos = set()
        for _ in range(40):
            html = page.content()
            key = hash(html)
            if key not in vistos:
                vistos.add(key)
                htmls.append(html)
            if not click_siguiente_visible(page):
                break
            page.wait_for_timeout(900)

        browser.close()
        return htmls


def obtener_html_renderizado(url: str) -> str:
    return obtener_htmls_renderizados(url)[0]


def fila_textos(tr) -> List[str]:
    celdas = tr.find_all(["th", "td"])
    return [normalizar(c.get_text(" ")) for c in celdas if normalizar(c.get_text(" "))]


def fila_textos_raw(tr) -> List[str]:
    # En resultados FEFI deja vacía la primera columna de la fila visitante.
    # Si filtramos vacíos se corren las columnas y aparece un número como rival.
    celdas = tr.find_all(["th", "td"])
    return [normalizar(c.get_text(" ")) for c in celdas]


def es_numero(v: str) -> bool:
    return bool(re.fullmatch(r"\d+", normalizar(v)))


def parsear_tablas(soup: BeautifulSoup, categorias: List[str]) -> Dict:
    resultado = {"general": [], "categorias": {c: [] for c in categorias}}
    seccion = None
    posibles_secciones = {"GENERAL": "general", **{canon(c): c for c in categorias}}

    for table in soup.find_all("table"):
        filas = [fila_textos(tr) for tr in table.find_all("tr")]
        for cells in filas:
            if not cells:
                continue
            if len(cells) == 1:
                key = canon(cells[0])
                if key in posibles_secciones:
                    seccion = posibles_secciones[key]
                continue
            header = [canon(c) for c in cells]
            if "EQUIPOS" in header and "PJ" in header and ("PTS" in header or "PTS." in [c.upper() for c in cells]):
                continue
            if seccion and len(cells) >= 6 and all(es_numero(x) for x in cells[-5:]):
                fila = {
                    "equipo": cells[0],
                    "pj": int(cells[-5]),
                    "g": int(cells[-4]),
                    "e": int(cells[-3]),
                    "p": int(cells[-2]),
                    "pts": int(cells[-1]),
                }
                if seccion == "general":
                    if fila not in resultado["general"]:
                        resultado["general"].append(fila)
                else:
                    if fila not in resultado["categorias"].setdefault(seccion, []):
                        resultado["categorias"][seccion].append(fila)
    return resultado


def fecha_id_desde_texto(valor: str) -> str:
    m = re.search(r"F(?:ECHA)?\s*(\d+)", str(valor), re.I)
    return f"F{m.group(1)}" if m else ""


def fixture_por_fecha(zona: str) -> Dict[str, Dict]:
    return {p.get("fecha_id") or fecha_id_desde_texto(p.get("fecha", "")): p for p in FIXTURES_FIJOS[zona]}


def buscar_fixture_por_equipos(zona: str, local: str, visitante: str, fecha_id: str = "") -> Optional[Dict]:
    fx = FIXTURES_FIJOS[zona]
    if fecha_id:
        for p in fx:
            if p.get("fecha_id") == fecha_id:
                return p
    cl, cv = canon(local), canon(visitante)
    for p in fx:
        if canon(p["local"]) == cl and canon(p["visitante"]) == cv:
            return p
    return None



def aliases_categoria(cat: str) -> List[str]:
    txt = normalizar(cat)
    aliases = {txt, txt.replace(' ', '')}
    partes = re.findall(r"\d+", txt)
    if partes:
        cortas = [x[-2:] for x in partes]
        aliases.add('/'.join(cortas))
        aliases.add(' / '.join(cortas))
        if len(partes) == 1:
            aliases.add(cortas[0])
        aliases.add('/'.join(partes))
        aliases.add(' / '.join(partes))
    return [canon(a) for a in aliases if a]


def buscar_posicion_categoria(header_canon: List[str], categoria: str) -> Optional[int]:
    posibles = set(aliases_categoria(categoria))
    for i, h in enumerate(header_canon):
        if h in posibles:
            return i
    return None


def valor_visible(v: str):
    v = normalizar(v)
    return None if v in ("", "-") else v


def alinear_fila_con_header(row: List[str], header: List[str]) -> List[str]:
    cells = [normalizar(c) for c in row]
    cells = [c for c in cells if canon(c) not in {"VERIFICADO", "PREVIO", "ESTADO"}]
    header_len = len(header)
    if len(cells) == header_len:
        return cells
    if len(cells) == header_len - 1 and (not cells or not fecha_id_desde_texto(cells[0])):
        return [""] + cells
    if len(cells) > header_len:
        return cells[:header_len]
    return cells + [""] * (header_len - len(cells))


def indice_header(header: List[str], opciones: set) -> Optional[int]:
    for i, h in enumerate(header):
        if h in opciones:
            return i
    return None


def parsear_fila_resultado_por_header(row: List[str], header_canon: List[str], categorias: List[str]) -> Optional[Dict]:
    cells = alinear_fila_con_header(row, header_canon)
    if not any(cells):
        return None
    idx_equipo = indice_header(header_canon, {"EQUIPOS", "EQUIPO"})
    idx_pj = indice_header(header_canon, {"PJ", "PJ."})
    idx_pts = indice_header(header_canon, {"PTS", "PTS."})
    if idx_equipo is None:
        return None
    fecha_id = ""
    idx_ft = indice_header(header_canon, {"FT", "FT.", "F.T", "F.T."})
    if idx_ft is not None and idx_ft < len(cells):
        fecha_id = fecha_id_desde_texto(cells[idx_ft])
    if not fecha_id and cells:
        fecha_id = fecha_id_desde_texto(cells[0])
    equipo = cells[idx_equipo] if idx_equipo < len(cells) else ""
    if not equipo or canon(equipo) in {"EQUIPOS", "EQUIPO"}:
        return None
    resultados_cat = []
    for cat in categorias:
        idx_cat = buscar_posicion_categoria(header_canon, cat)
        valor = None
        if idx_cat is not None and idx_cat < len(cells):
            valor = valor_visible(cells[idx_cat])
        resultados_cat.append(valor)
    pj_val = cells[idx_pj] if idx_pj is not None and idx_pj < len(cells) else ""
    pts_val = cells[idx_pts] if idx_pts is not None and idx_pts < len(cells) else ""
    return {
        "fecha_id": fecha_id,
        "equipo": equipo,
        "categorias": resultados_cat,
        "pj": int(pj_val) if es_numero(pj_val) else None,
        "pts": int(pts_val) if es_numero(pts_val) else None,
    }

def parsear_resultados(soup: BeautifulSoup, zona: str, categorias: List[str]) -> Dict:
    general: Dict[str, List[Dict]] = {}
    equipo_propio = canon(ZONAS[zona]["equipo"])

    for table in soup.find_all("table"):
        filas = [fila_textos_raw(tr) for tr in table.find_all("tr")]
        if not filas:
            continue

        header_idx = -1
        for idx, cells in enumerate(filas):
            h = [canon(c) for c in cells]
            tiene_equipo = "EQUIPOS" in h
            tiene_pj = any(x in {"PJ", "PJ."} for x in h)
            tiene_pts = any(x in {"PTS", "PTS."} for x in h)
            tiene_categoria = any(buscar_posicion_categoria(h, cat) is not None for cat in categorias)
            if tiene_equipo and tiene_categoria and tiene_pj and tiene_pts:
                header_idx = idx
                break
        if header_idx == -1:
            continue

        rows = filas[header_idx + 1:]
        i = 0
        while i < len(rows) - 1:
            header_canon = [canon(c) for c in filas[header_idx]]
            fila_local = parsear_fila_resultado_por_header(rows[i], header_canon, categorias)
            fila_visitante = parsear_fila_resultado_por_header(rows[i + 1], header_canon, categorias)
            if not fila_local or not fila_visitante:
                i += 1
                continue

            fecha_id = fila_local.get("fecha_id") or fila_visitante.get("fecha_id")
            local = fila_local.get("equipo", "")
            visitante = fila_visitante.get("equipo", "")

            if not local or not visitante:
                i += 1
                continue
            if equipo_propio not in canon(local) and equipo_propio not in canon(visitante):
                i += 2
                continue

            fx = buscar_fixture_por_equipos(zona, local, visitante, fecha_id)
            if not fx and fecha_id in fixture_por_fecha(zona):
                fx = fixture_por_fecha(zona)[fecha_id]

            resultados = {}
            tiene_alguno = False
            for idx_cat, cat in enumerate(categorias):
                val_local = fila_local["categorias"][idx_cat] if idx_cat < len(fila_local["categorias"]) else None
                val_visitante = fila_visitante["categorias"][idx_cat] if idx_cat < len(fila_visitante["categorias"]) else None
                if val_local is not None or val_visitante is not None:
                    tiene_alguno = True
                resultados[cat] = {"local": val_local, "visitante": val_visitante}

            if not tiene_alguno and fila_local.get("pts") is None and fila_visitante.get("pts") is None:
                i += 2
                continue

            partido = {
                "fecha_id": fecha_id or (fx or {}).get("fecha_id", ""),
                "fecha": (fx or {}).get("fecha", fecha_id),
                "local": (fx or {}).get("local", local),
                "visitante": (fx or {}).get("visitante", visitante),
                "pj_local": fila_local.get("pj"),
                "pts_local": fila_local.get("pts"),
                "pj_visitante": fila_visitante.get("pj"),
                "pts_visitante": fila_visitante.get("pts"),
                "resultados": resultados,
            }
            fid = partido["fecha_id"] or fecha_id or "SIN_FECHA"
            general.setdefault(fid, []).append(partido)
            i += 2

    return {"general": general, "categorias": {}}


def actualizar_desde_fefi():
    asegurar_fixture_y_archivos_base()
    for zona, cfg in ZONAS.items():
        print(f"Actualizando {zona}: {cfg['url']}")
        htmls = obtener_htmls_renderizados(cfg["url"])
        tabla = {"general": [], "categorias": {c: [] for c in cfg["categorias"]}}
        resultados = {"general": {}, "categorias": {}}

        for html in htmls:
            soup = BeautifulSoup(html, "html.parser")

            tabla_tmp = parsear_tablas(soup, cfg["categorias"])
            for fila in tabla_tmp.get("general", []):
                if fila not in tabla["general"]:
                    tabla["general"].append(fila)
            for cat, filas in (tabla_tmp.get("categorias") or {}).items():
                tabla["categorias"].setdefault(cat, [])
                for fila in filas:
                    if fila not in tabla["categorias"][cat]:
                        tabla["categorias"][cat].append(fila)

            res_tmp = parsear_resultados(soup, zona, cfg["categorias"])
            for fid, partidos in (res_tmp.get("general") or {}).items():
                resultados["general"].setdefault(fid, [])
                existentes = {
                    (p.get("fecha_id"), canon(p.get("local", "")), canon(p.get("visitante", "")))
                    for p in resultados["general"][fid]
                }
                for partido in partidos:
                    clave_partido = (partido.get("fecha_id"), canon(partido.get("local", "")), canon(partido.get("visitante", "")))
                    if clave_partido not in existentes:
                        resultados["general"][fid].append(partido)
                        existentes.add(clave_partido)

        base = Path("data") / zona
        # Importante: solo pisamos si encontró datos. Así no rompe lo anterior con vacíos.
        if tabla["general"] or any(tabla["categorias"].values()):
            guardar_json(base / "tabla.json", tabla)
        else:
            print("  AVISO: no encontré tablas renderizadas. No piso tabla.json.")

        if resultados["general"]:
            guardar_json(base / "resultados.json", resultados)
        else:
            print("  AVISO: no encontré resultados renderizados. No piso resultados.json.")

        fixture = leer_json(base / "fixture.json", [])
        tabla_guardada = leer_json(base / "tabla.json", {"general": []})
        res_guardado = leer_json(base / "resultados.json", {"general": {}})
        direcciones = leer_json(base / "direcciones.json", {})
        print(f"Zona {zona}: fixture={len(fixture)} | tabla_general={len(tabla_guardada.get('general', []))} | resultados={len(res_guardado.get('general', {}))} | direcciones={len(direcciones)}")


def main():
    if len(sys.argv) > 1 and sys.argv[1].lower() == "actualizar":
        actualizar_desde_fefi()
        print("\nLISTO. Se intentó actualizar desde FEFI sin pisar datos con vacíos.")
    else:
        asegurar_fixture_y_archivos_base()
        print("LISTO. Modo fijo. No se conectó a FEFI.")
        print("Para actualizar tablas/resultados manualmente: python scraper.py actualizar")


if __name__ == "__main__":
    main()
