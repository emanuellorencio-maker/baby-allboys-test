import json
import os
import subprocess
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path


class handler(BaseHTTPRequestHandler):
    def _json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        root = Path(__file__).resolve().parent.parent
        comando = [sys.executable, "scraper.py", "tablas"]

        print("actualizar-tablas: inicio de actualizacion")
        print(f"actualizar-tablas: cwd={root}")
        print(f"actualizar-tablas: comando={' '.join(comando)}")

        try:
            proceso = subprocess.run(
                comando,
                cwd=root,
                capture_output=True,
                text=True,
                timeout=120,
                env={**os.environ, "PYTHONUTF8": "1"},
            )
        except Exception as error:
            print(f"actualizar-tablas: error al ejecutar scraper: {error}")
            self._json(500, {"ok": False, "error": str(error)})
            return

        salida = proceso.stdout or ""
        error = proceso.stderr or ""
        zonas = [linea.strip() for linea in salida.splitlines() if linea.startswith("Zona ")]

        print("actualizar-tablas: salida del scraper")
        print(salida)
        if error:
            print("actualizar-tablas: stderr del scraper")
            print(error)

        if proceso.returncode != 0:
            print(f"actualizar-tablas: termino con error rc={proceso.returncode}")
            self._json(
                500,
                {
                    "ok": False,
                    "returncode": proceso.returncode,
                    "zonas": zonas,
                    "stdout": salida,
                    "stderr": error,
                },
            )
            return

        print("actualizar-tablas: termino bien")
        self._json(
            200,
            {
                "ok": True,
                "returncode": proceso.returncode,
                "zonas": zonas,
                "stdout": salida,
                "stderr": error,
            },
        )
