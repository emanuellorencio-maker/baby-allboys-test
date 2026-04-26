from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os

ARCHIVO = os.path.join("data", "resultados_manual.json")

class Handler(BaseHTTPRequestHandler):
    def enviar_headers(self, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self.enviar_headers(200)
        self.wfile.write(b'{"ok": true}')

    def do_GET(self):
        self.enviar_headers(200)
        self.wfile.write(json.dumps({
            "ok": True,
            "mensaje": "Servidor de guardado funcionando",
            "archivo": ARCHIVO
        }, ensure_ascii=False).encode("utf-8"))

    def do_POST(self):
        if self.path != "/guardar":
            self.enviar_headers(404)
            self.wfile.write(json.dumps({
                "ok": False,
                "error": "Ruta no encontrada"
            }, ensure_ascii=False).encode("utf-8"))
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body)

            os.makedirs("data", exist_ok=True)

            with open(ARCHIVO, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self.enviar_headers(200)
            self.wfile.write(json.dumps({
                "ok": True,
                "archivo": ARCHIVO
            }, ensure_ascii=False).encode("utf-8"))

        except Exception as e:
            self.enviar_headers(500)
            self.wfile.write(json.dumps({
                "ok": False,
                "error": str(e)
            }, ensure_ascii=False).encode("utf-8"))

if __name__ == "__main__":
    print("Servidor de guardado funcionando en http://127.0.0.1:8001")
    print("No cierres esta ventana mientras uses el admin.")
    HTTPServer(("127.0.0.1", 8001), Handler).serve_forever()
