import json
import os
import re
import shutil
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"

FIXTURES = {
    "c": [
        {"fecha":"Fecha 1 - 18 de Abril","local":"ALL BOYS \"A\"","visitante":"PUEYRREDON","condicion":"Local"},
        {"fecha":"Fecha 2 - 25 de Abril","local":"C. S. D. PARQUE","visitante":"ALL BOYS \"A\"","condicion":"Visitante"},
        {"fecha":"Fecha 3 - 02 de Mayo","local":"ALL BOYS \"A\"","visitante":"BICHOS COLORADOS","condicion":"Local"},
        {"fecha":"Fecha 4 - 09 de Mayo","local":"CLUB OESTE","visitante":"ALL BOYS \"A\"","condicion":"Visitante"},
        {"fecha":"Fecha 5 - 16 de Mayo","local":"ALL BOYS \"A\"","visitante":"DON BOSCO","condicion":"Local"},
        {"fecha":"Fecha 6 - 23 de Mayo","local":"CENTRO ESPAÑOL","visitante":"ALL BOYS \"A\"","condicion":"Visitante"},
        {"fecha":"Fecha 7 - 30 de Mayo","local":"ALL BOYS \"A\"","visitante":"U.D.S. ALLENDE","condicion":"Local"},
        {"fecha":"Fecha 8 - 06 de Junio","local":"RACING CLUB 1","visitante":"ALL BOYS \"A\"","condicion":"Visitante"},
        {"fecha":"Fecha 9 - 13 de Junio","local":"ALL BOYS \"A\"","visitante":"ESTRELLA DE MALDONADO ''B''","condicion":"Local"},
        {"fecha":"Fecha 10 - 20 de Junio","local":"LOS CAMBOYANOS","visitante":"ALL BOYS \"A\"","condicion":"Visitante"},
        {"fecha":"Fecha 11 - 27 de Junio","local":"ALL BOYS \"A\"","visitante":"INDEPENDIENTE DE HURLINGHAM","condicion":"Local"},
        {"fecha":"Fecha 12 - 04 de Julio","local":"ALL BOYS \"A\"","visitante":"MARIANO MORENO","condicion":"Local"},
        {"fecha":"Fecha 13 - 11 de Julio","local":"SANTIAGO DE LINIERS","visitante":"ALL BOYS \"A\"","condicion":"Visitante"},
        {"fecha":"Fecha 14 - 18 de Julio","local":"ALL BOYS \"A\"","visitante":"INDEPENDIENTE","condicion":"Local"},
        {"fecha":"Fecha 15 - 01 de Agosto","local":"D. F. SARMIENTO","visitante":"ALL BOYS \"A\"","condicion":"Visitante"}
    ],
    "i": [
        {"fecha":"Fecha 1 - 18 de Abril","local":"SOLDATI 32 F. C.","visitante":"ALL BOYS \"B\"","condicion":"Visitante"},
        {"fecha":"Fecha 2 - 25 de Abril","local":"ALL BOYS \"B\"","visitante":"CLUB CIENCIA Y LABOR","condicion":"Local"},
        {"fecha":"Fecha 3 - 02 de Mayo","local":"VILLA REAL ROJO","visitante":"ALL BOYS \"B\"","condicion":"Visitante"},
        {"fecha":"Fecha 4 - 09 de Mayo","local":"ALL BOYS \"B\"","visitante":"MARCHIGIANA","condicion":"Local"},
        {"fecha":"Fecha 5 - 16 de Mayo","local":"LUJAN DE LOS PATRIOTAS","visitante":"ALL BOYS \"B\"","condicion":"Visitante"},
        {"fecha":"Fecha 6 - 23 de Mayo","local":"ALL BOYS \"B\"","visitante":"LA MARCA","condicion":"Local"},
        {"fecha":"Fecha 7 - 30 de Mayo","local":"LUGANO TENNIS CLUB","visitante":"ALL BOYS \"B\"","condicion":"Visitante"},
        {"fecha":"Fecha 8 - 06 de Junio","local":"ALL BOYS \"B\"","visitante":"EL TREBOL F. C.","condicion":"Local"},
        {"fecha":"Fecha 9 - 13 de Junio","local":"LOS ANDES","visitante":"ALL BOYS \"B\"","condicion":"Visitante"},
        {"fecha":"Fecha 10 - 20 de Junio","local":"ALL BOYS \"B\"","visitante":"AÑASCO","condicion":"Local"},
        {"fecha":"Fecha 11 - 27 de Junio","local":"LIGA FOMENTO VILLA MITRE","visitante":"ALL BOYS \"B\"","condicion":"Visitante"},
        {"fecha":"Fecha 12 - 04 de Julio","local":"K. A. C.","visitante":"ALL BOYS \"B\"","condicion":"Visitante"},
        {"fecha":"Fecha 13 - 11 de Julio","local":"ALL BOYS \"B\"","visitante":"HURACAN","condicion":"Local"},
        {"fecha":"Fecha 14 - 18 de Julio","local":"LOMAS BLANCO","visitante":"ALL BOYS \"B\"","condicion":"Visitante"},
        {"fecha":"Fecha 15 - 01 de Agosto","local":"ALL BOYS \"B\"","visitante":"FATIMA","condicion":"Local"}
    ],
    "mat1": [
        {"fecha":"Fecha 1 - 18 de Abril","local":"LOS ALBOS","visitante":"LOS CUERVOS","condicion":"Local"},
        {"fecha":"Fecha 2 - 25 de Abril","local":"NUEVA CHICAGO","visitante":"LOS ALBOS","condicion":"Visitante"},
        {"fecha":"Fecha 3 - 02 de Mayo","local":"LOS ALBOS","visitante":"SANELI F.C.","condicion":"Local"},
        {"fecha":"Fecha 4 - 09 de Mayo","local":"CLUB PACIFICO","visitante":"LOS ALBOS","condicion":"Visitante"},
        {"fecha":"Fecha 5 - 16 de Mayo","local":"LOS ALBOS","visitante":"CLUB AT. LUGANO","condicion":"Local"},
        {"fecha":"Fecha 6 - 23 de Mayo","local":"VILLA LURO NORTE","visitante":"LOS ALBOS","condicion":"Visitante"},
        {"fecha":"Fecha 7 - 30 de Mayo","local":"LOS ALBOS","visitante":"FLORES CLUB","condicion":"Local"},
        {"fecha":"Fecha 8 - 06 de Junio","local":"LOS ALBOS","visitante":"VILLA HERMINIA","condicion":"Local"},
        {"fecha":"Fecha 9 - 13 de Junio","local":"PLATENSE BLANCO","visitante":"LOS ALBOS","condicion":"Visitante"},
        {"fecha":"Fecha 10 - 20 de Junio","local":"LOS ALBOS","visitante":"A. A. A. J.","condicion":"Local"},
        {"fecha":"Fecha 11 - 27 de Junio","local":"C. A. VIRGEN DEL CARMEN","visitante":"LOS ALBOS","condicion":"Visitante"},
        {"fecha":"Fecha 12 - 04 de Julio","local":"LOS ALBOS","visitante":"EST. PORTEÑO ROJO","condicion":"Local"},
        {"fecha":"Fecha 13 - 11 de Julio","local":"C. S. y D. PAMPERO","visitante":"LOS ALBOS","condicion":"Visitante"},
        {"fecha":"Fecha 14 - 18 de Julio","local":"LOS ALBOS","visitante":"ESTRELLA DE BOEDO","condicion":"Local"},
        {"fecha":"Fecha 15 - 01 de Agosto","local":"CLUB LA PATERNAL","visitante":"LOS ALBOS","condicion":"Visitante"}
    ],
    "mat4": [
        {"fecha":"Fecha 1 - 18 de Abril","local":"LOS CARASUCIAS","visitante":"ALL BOYS","condicion":"Visitante"},
        {"fecha":"Fecha 2 - 25 de Abril","local":"ALL BOYS","visitante":"ALMAFUERTE FUTBOL CLUB","condicion":"Local"},
        {"fecha":"Fecha 3 - 02 de Mayo","local":"EROS","visitante":"ALL BOYS","condicion":"Visitante"},
        {"fecha":"Fecha 4 - 09 de Mayo","local":"ALL BOYS","visitante":"ALVEAR","condicion":"Local"},
        {"fecha":"Fecha 5 - 16 de Mayo","local":"C. A. ATLANTA","visitante":"ALL BOYS","condicion":"Visitante"},
        {"fecha":"Fecha 6 - 23 de Mayo","local":"ALL BOYS","visitante":"C. A. VERSAILLES BLANCO","condicion":"Local"},
        {"fecha":"Fecha 7 - 30 de Mayo","local":"V. L. N.","visitante":"ALL BOYS","condicion":"Visitante"},
        {"fecha":"Fecha 8 - 06 de Junio","local":"CE. F. F. LA INDEPENDENCIA","visitante":"ALL BOYS","condicion":"Visitante"},
        {"fecha":"Fecha 9 - 13 de Junio","local":"ALL BOYS","visitante":"COMPLEJO COSTAS CELESTE","condicion":"Local"},
        {"fecha":"Fecha 10 - 20 de Junio","local":"PARQUE PATRICIOS","visitante":"ALL BOYS","condicion":"Visitante"},
        {"fecha":"Fecha 11 - 27 de Junio","local":"ALL BOYS","visitante":"EL TIFON DE BOYACA","condicion":"Local"},
        {"fecha":"Fecha 12 - 04 de Julio","local":"CICLON FORTIN","visitante":"ALL BOYS","condicion":"Visitante"},
        {"fecha":"Fecha 13 - 11 de Julio","local":"ALL BOYS","visitante":"SP. PEREYRA","condicion":"Local"},
        {"fecha":"Fecha 14 - 18 de Julio","local":"HURACAN TIKI TIKI","visitante":"ALL BOYS","condicion":"Visitante"},
        {"fecha":"Fecha 15 - 01 de Agosto","local":"ALL BOYS","visitante":"C. A. ESTUDIANTES","condicion":"Local"}
    ]
}

CATEGORIAS = {
    "c": ["2019", "2013", "2018", "2014", "2017", "2016", "2015"],
    "i": ["2019", "2013", "2018", "2014", "2017", "2016", "2015"],
    "mat1": ["2013", "2014/15", "2016/17", "2018/19", "2020/21/22"],
    "mat4": ["2013", "2014", "2015", "2016", "2017", "2018/19/20"],
}


def fecha_id(texto):
    m = re.search(r"Fecha\s+(\d+)", str(texto), re.I)
    return f"F{m.group(1)}" if m else ""


def leer_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def guardar_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def esta_vacio_json(data):
    if data is None:
        return True
    if isinstance(data, list):
        return len(data) == 0
    if isinstance(data, dict):
        general = data.get("general")
        categorias = data.get("categorias")
        if isinstance(general, dict) and general:
            return False
        if isinstance(general, list) and general:
            return False
        if isinstance(categorias, dict):
            for v in categorias.values():
                if v:
                    return False
        return True
    return False


def copiar_manual_si_existe(zona, nombre_archivo):
    destino = DATA / zona / nombre_archivo
    posibles = [
        BASE / f"{nombre_archivo.replace('.json','')}_{zona}.json",
        BASE / f"{nombre_archivo.replace('.json','')}_{zona}_fixed.json",
        BASE / nombre_archivo,
    ]
    actual = leer_json(destino)
    if not esta_vacio_json(actual):
        return "conservado"
    for src in posibles:
        if src.exists():
            data = leer_json(src)
            if not esta_vacio_json(data):
                guardar_json(destino, data)
                return f"copiado desde {src.name}"
    return "plantilla vacía"


def main():
    DATA.mkdir(exist_ok=True)
    for zona, fixture in FIXTURES.items():
        carpeta = DATA / zona
        carpeta.mkdir(parents=True, exist_ok=True)

        fixture_final = []
        for p in fixture:
            item = dict(p)
            item["fecha_id"] = fecha_id(item.get("fecha", ""))
            fixture_final.append(item)
        guardar_json(carpeta / "fixture.json", fixture_final)

        tabla_path = carpeta / "tabla.json"
        if not tabla_path.exists() or esta_vacio_json(leer_json(tabla_path)):
            guardar_json(tabla_path, {"general": [], "categorias": {c: [] for c in CATEGORIAS[zona]}})

        resultados_path = carpeta / "resultados.json"
        if not resultados_path.exists() or esta_vacio_json(leer_json(resultados_path)):
            guardar_json(resultados_path, {"general": {}})

        if not (carpeta / "direcciones.json").exists():
            guardar_json(carpeta / "direcciones.json", {})

        tabla_estado = copiar_manual_si_existe(zona, "tabla.json")
        resultados_estado = copiar_manual_si_existe(zona, "resultados.json")
        tabla = leer_json(carpeta / "tabla.json") or {}
        resultados = leer_json(carpeta / "resultados.json") or {}
        print(f"Zona {zona}: fixture={len(fixture_final)} | tabla_general={len(tabla.get('general', [])) if isinstance(tabla.get('general'), list) else len(tabla.get('general', {}))} | resultados={len(resultados.get('general', {}))} | tabla={tabla_estado} | resultados={resultados_estado}")

    print("\nLISTO. No se descarga FEFI. El fixture queda fijo y no se pisa más con 0.")
    print("Cuando tengas tabla/resultados manuales, pegá los JSON en data/<zona>/tabla.json o data/<zona>/resultados.json.")


if __name__ == "__main__":
    main()
