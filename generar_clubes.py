import json
import re
import unicodedata
from pathlib import Path


ZONAS = ("c", "i", "mat1", "mat4")
DATA_DIR = Path("data")
CLUBES_PATH = DATA_DIR / "clubes.json"
ESCUDOS_DIR = Path("assets") / "escudos"
ESCUDO_FORMATOS = ("png", "jpg", "svg")


def normalizar_texto(valor: str) -> str:
    return " ".join(str(valor or "").strip().split())


def reparar_mojibake(valor: str) -> str:
    texto = normalizar_texto(valor)
    if "Ã" not in texto and "Â" not in texto:
        return texto
    try:
        reparado = texto.encode("latin1").decode("utf-8")
        return normalizar_texto(reparado)
    except Exception:
        return texto


def sin_acentos(valor: str) -> str:
    texto = unicodedata.normalize("NFD", valor)
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def slugificar(nombre: str) -> str:
    texto = reparar_mojibake(nombre).lower()
    texto = sin_acentos(texto)
    texto = texto.replace('"', "").replace("'", "")
    texto = re.sub(r"[^a-z0-9]+", "-", texto)
    return texto.strip("-")


def alias_base(nombre: str) -> list[str]:
    alias = []
    original = normalizar_texto(nombre)
    reparado = reparar_mojibake(original)
    sin_comillas = normalizar_texto(reparado.replace('"', "").replace("'", ""))
    for item in (sin_comillas, reparado, original):
        if item and item not in alias:
            alias.append(item)
    return alias


def leer_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def guardar_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def clubes_desde_fixtures() -> dict[str, str]:
    clubes = {}
    for zona in ZONAS:
        path = DATA_DIR / zona / "fixture.json"
        fixture = leer_json(path, [])
        if not isinstance(fixture, list):
            raise ValueError(f"Fixture invalido: {path}")
        for partido in fixture:
            for campo in ("local", "visitante"):
                nombre = normalizar_texto(partido.get(campo, ""))
                if not nombre:
                    continue
                slug = slugificar(nombre)
                if not slug:
                    continue
                clubes.setdefault(slug, reparar_mojibake(nombre))
    return clubes


def indexar_existentes(data) -> dict[str, dict]:
    existentes = {}
    if not isinstance(data, list):
        return existentes
    for item in data:
        if not isinstance(item, dict):
            continue
        slug = item.get("slug") or slugificar(item.get("nombre", ""))
        if not slug:
            continue
        item["slug"] = slug
        existentes[slug] = item
    return existentes


def escudo_para_slug(slug: str, actual: str = "") -> str:
    if actual:
        actual_path = Path(actual)
        if actual_path.exists():
            return actual

    for ext in ESCUDO_FORMATOS:
        candidato = ESCUDOS_DIR / f"{slug}.{ext}"
        if candidato.exists():
            return candidato.as_posix()

    return (ESCUDOS_DIR / f"{slug}.png").as_posix()


def fusionar_clubes(nuevos: dict[str, str], existentes: dict[str, dict]) -> list[dict]:
    resultado = {}
    for slug, nombre in nuevos.items():
        item = dict(existentes.get(slug, {}))
        item.setdefault("nombre", nombre)
        item.setdefault("slug", slug)
        item["escudo"] = escudo_para_slug(slug, item.get("escudo", ""))

        aliases = []
        for alias in item.get("alias", []):
            alias_limpio = normalizar_texto(alias)
            if alias_limpio and alias_limpio not in aliases:
                aliases.append(alias_limpio)
        for alias in alias_base(nombre):
            if alias not in aliases:
                aliases.append(alias)
        item["alias"] = aliases

        resultado[slug] = item

    for slug, item in existentes.items():
        if slug not in resultado:
            resultado[slug] = item

    return sorted(
        resultado.values(),
        key=lambda club: sin_acentos(str(club.get("nombre", ""))).lower(),
    )


def validar_cobertura(clubes: list[dict], esperados: dict[str, str]):
    slugs = {club.get("slug") for club in clubes}
    faltantes = sorted(nombre for slug, nombre in esperados.items() if slug not in slugs)
    if faltantes:
        raise RuntimeError("Faltan clubes en data/clubes.json: " + ", ".join(faltantes))


def main():
    ESCUDOS_DIR.mkdir(parents=True, exist_ok=True)
    nuevos = clubes_desde_fixtures()
    existentes = indexar_existentes(leer_json(CLUBES_PATH, []))
    clubes = fusionar_clubes(nuevos, existentes)
    validar_cobertura(clubes, nuevos)
    guardar_json(CLUBES_PATH, clubes)
    print(f"Clubes detectados en fixtures: {len(nuevos)}")
    print(f"Clubes guardados en {CLUBES_PATH}: {len(clubes)}")
    print(f"Carpeta de escudos lista: {ESCUDOS_DIR}")


if __name__ == "__main__":
    main()
