import json
import re
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from urllib.error import URLError, HTTPError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

SOURCE_URL = "https://caallboys.com.ar/actualidad/"
OUTPUT_PATH = Path("data/noticias.json")
MAX_ITEMS = 8


def normalizar_texto(valor: str) -> str:
    texto = unescape(str(valor or ""))
    texto = re.sub(r"<[^>]+>", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def es_link_valido(url: str) -> bool:
    try:
        p = urlparse(url)
    except Exception:
        return False
    return p.scheme in {"http", "https"} and bool(p.netloc)


def extraer_fecha(texto: str, link: str) -> str:
    m_texto = re.search(r"(\d{1,2})[\/-](\d{1,2})[\/-](\d{4})", texto or "")
    if m_texto:
        dia, mes, anio = m_texto.groups()
        return f"{int(anio):04d}-{int(mes):02d}-{int(dia):02d}"

    m_link = re.search(r"/(20\d{2})/(\d{2})/(\d{2})/", link or "")
    if m_link:
        anio, mes, dia = m_link.groups()
        return f"{anio}-{mes}-{dia}"

    return ""


def parsear_noticias_regex(html: str):
    pattern = re.compile(
        r"<h[23][^>]*>[\s\S]*?<a[^>]+href=[\"']([^\"']+)[\"'][^>]*>([\s\S]*?)</a>[\s\S]*?</h[23]>",
        re.IGNORECASE,
    )
    noticias, vistos = [], set()

    for m in pattern.finditer(html):
        link = urljoin(SOURCE_URL, normalizar_texto(m.group(1)))
        if not es_link_valido(link) or "caallboys.com.ar" not in link:
            continue
        if link in vistos or not re.search(r"/20\d{2}/\d{2}/\d{2}/", link):
            continue

        titulo = normalizar_texto(m.group(2))
        if not titulo:
            continue

        contexto = html[max(0, m.start() - 400): m.end() + 800]
        fecha = extraer_fecha(contexto, link)

        desc_match = re.search(r"<p[^>]*>(.*?)</p>", contexto, re.IGNORECASE | re.DOTALL)
        descripcion = normalizar_texto(desc_match.group(1)) if desc_match else ""
        if not descripcion:
            descripcion = f"Nota oficial publicada por el Club Atlético All Boys: {titulo}."

        noticias.append(
            {
                "tag": "Actualidad",
                "fecha": fecha,
                "titulo": titulo,
                "descripcion": descripcion,
                "link": link,
            }
        )
        vistos.add(link)

        if len(noticias) >= MAX_ITEMS:
            break

    return noticias


def validar_formato(items):
    salida = []
    for item in items:
        if not isinstance(item, dict):
            continue

        titulo = normalizar_texto(item.get("titulo", ""))
        link = normalizar_texto(item.get("link", ""))
        if not titulo or not es_link_valido(link):
            continue

        salida.append(
            {
                "tag": normalizar_texto(item.get("tag", "Actualidad")) or "Actualidad",
                "fecha": normalizar_texto(item.get("fecha", "")),
                "titulo": titulo,
                "descripcion": normalizar_texto(item.get("descripcion", ""))
                or f"Nota oficial publicada por el Club Atlético All Boys: {titulo}.",
                "link": link,
            }
        )

    dedup, vistos = [], set()
    for item in salida:
        if item["link"] in vistos:
            continue
        vistos.add(item["link"])
        dedup.append(item)

    return dedup


def cargar_previas():
    if not OUTPUT_PATH.exists():
        return []
    try:
        data = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []
    return validar_formato(data if isinstance(data, list) else [])


def fallback():
    hoy = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return [
        {
            "tag": "Actualidad",
            "fecha": hoy,
            "titulo": "Visitá la actualidad oficial de All Boys",
            "descripcion": "No se pudo actualizar automáticamente. Entrá al sitio oficial para ver las últimas noticias.",
            "link": SOURCE_URL,
        },
        {
            "tag": "Institucional",
            "fecha": hoy,
            "titulo": "Portal oficial del Club Atlético All Boys",
            "descripcion": "Accedé a comunicados, agenda y novedades institucionales del club.",
            "link": "https://caallboys.com.ar/",
        },
        {
            "tag": "Redes",
            "fecha": hoy,
            "titulo": "Instagram oficial de All Boys",
            "descripcion": "Seguimiento diario con contenidos y anuncios del club.",
            "link": "https://www.instagram.com/caallboys/",
        },
    ]


def descargar_html():
    req = Request(SOURCE_URL, headers={"User-Agent": "baby-allboys-test/1.0"})
    with urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def main():
    noticias = []
    try:
        html = descargar_html()
        noticias = parsear_noticias_regex(html)
    except (URLError, HTTPError, TimeoutError, OSError):
        noticias = []

    noticias = validar_formato(noticias)

    if len(noticias) < 3:
        noticias.extend(cargar_previas())
        noticias = validar_formato(noticias)

    if len(noticias) < 3:
        noticias = validar_formato(fallback() + noticias)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(noticias[:MAX_ITEMS], ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Noticias guardadas: {len(noticias[:MAX_ITEMS])} en {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
