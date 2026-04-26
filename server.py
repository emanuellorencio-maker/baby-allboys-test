from http.server import BaseHTTPRequestHandler, HTTPServer
import json, os, subprocess

ARCHIVO = os.path.join("data", "resultados_manual.json")

class Handler(BaseHTTPRequestHandler):

    def _headers(self, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._headers()

    def do_POST(self):
        if self.path != "/guardar":
            self._headers(404)
            return

        length = int(self.headers.get('Content-Length', 0))
        data = json.loads(self.rfile.read(length))

        os.makedirs("data", exist_ok=True)

        with open(ARCHIVO, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # 🔥 AUTOCOMMIT + PUSH
        try:
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", "update resultados automatico"], check=True)
            subprocess.run(["git", "push"], check=True)
        except:
            pass

        self._headers()
        self.wfile.write(json.dumps({"ok": True}).encode())

print("Server con autocommit activo en 8010")
HTTPServer(("127.0.0.1", 8010), Handler).serve_forever()
