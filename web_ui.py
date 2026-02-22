from __future__ import annotations

import cgi
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from tempfile import NamedTemporaryFile

from pipeline import estimate_from_image_and_utc


HTML_FORM = """<!doctype html>
<html lang='tr'>
<head><meta charset='utf-8'><title>Polar Star Navigator</title></head>
<body style='font-family: Arial; max-width: 720px; margin: 2rem auto;'>
  <h2>Fotoğraf + Tarih ile Konum Tahmini (MVP)</h2>
  <p>Sadece iki giriş var: <b>gökyüzü fotoğrafı</b> ve <b>UTC tarih/saat</b>.</p>
  <form method='POST' enctype='multipart/form-data'>
    <label>UTC Tarih/Saat:</label><br>
    <input name='utc' type='text' value='2026-01-15T22:30:00Z' style='width: 100%; padding: 8px;'><br><br>
    <label>Fotoğraf:</label><br>
    <input name='image' type='file' accept='image/*'><br><br>
    <button type='submit'>Hesapla</button>
  </form>
  {result_block}
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def _send_html(self, content: str) -> None:
        data = content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):  # noqa: N802
        self._send_html(HTML_FORM.format(result_block=""))

    def do_POST(self):  # noqa: N802
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": self.headers.get("Content-Type", "")},
        )
        utc = form.getfirst("utc", "").strip()
        image_item = form["image"] if "image" in form else None

        if not utc or image_item is None or not getattr(image_item, "file", None):
            self._send_html(HTML_FORM.format(result_block="<p style='color:red'>UTC ve fotoğraf zorunlu.</p>"))
            return

        suffix = Path(getattr(image_item, "filename", "upload.jpg") or "upload.jpg").suffix or ".jpg"
        with NamedTemporaryFile(suffix=suffix, delete=True) as tmp:
            tmp.write(image_item.file.read())
            tmp.flush()
            try:
                _, result = estimate_from_image_and_utc(tmp.name, utc)
                result_html = (
                    f"<hr><h3>Sonuç</h3>"
                    f"<p><b>Enlem:</b> {result.latitude_deg:.5f}°</p>"
                    f"<p><b>Boylam:</b> Hesaplanamadı (MVP)</p>"
                    f"<p><b>Güven:</b> {result.confidence:.2f}</p>"
                    f"<p><b>Not:</b> {result.note}</p>"
                )
            except Exception as exc:
                result_html = f"<p style='color:red'>Hata: {exc}</p>"

        self._send_html(HTML_FORM.format(result_block=result_html))


def run_server(port: int = 8000) -> None:
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"Web arayüz hazır: http://localhost:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
