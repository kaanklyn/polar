from __future__ import annotations

from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from tempfile import mkstemp
import os
from typing import Dict, Tuple

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


def _parse_multipart(content_type: str, body: bytes) -> Dict[str, Tuple[str | None, bytes]]:
    """Minimal multipart/form-data parser.

    Returns: {field_name: (filename_or_none, value_bytes)}
    """
    marker = "boundary="
    if marker not in content_type:
        raise ValueError("multipart boundary bulunamadı")

    boundary = content_type.split(marker, 1)[1].strip().strip('"')
    boundary_bytes = ("--" + boundary).encode("utf-8")

    fields: Dict[str, Tuple[str | None, bytes]] = {}
    parts = body.split(boundary_bytes)
    for part in parts:
        part = part.strip()
        if not part or part == b"--":
            continue

        if part.endswith(b"--"):
            part = part[:-2].strip()

        if b"\r\n\r\n" not in part:
            continue

        header_block, value = part.split(b"\r\n\r\n", 1)
        headers = header_block.decode("utf-8", errors="ignore").split("\r\n")
        value = value.rstrip(b"\r\n")

        disp = next((h for h in headers if h.lower().startswith("content-disposition:")), "")
        if "name=" not in disp:
            continue

        def _extract_param(text: str, key: str) -> str | None:
            token = key + '="'
            if token not in text:
                return None
            rest = text.split(token, 1)[1]
            return rest.split('"', 1)[0]

        name = _extract_param(disp, "name")
        filename = _extract_param(disp, "filename")
        if not name:
            continue

        fields[name] = (filename, value)

    return fields


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
        content_length = int(self.headers.get("Content-Length", "0"))
        content_type = self.headers.get("Content-Type", "")

        if content_length <= 0 or "multipart/form-data" not in content_type:
            self._send_html(HTML_FORM.format(result_block="<p style='color:red'>Geçersiz istek.</p>"))
            return

        body = self.rfile.read(content_length)

        try:
            fields = _parse_multipart(content_type, body)
        except Exception as exc:
            self._send_html(HTML_FORM.format(result_block=f"<p style='color:red'>Form ayrıştırma hatası: {exc}</p>"))
            return

        utc_bytes = fields.get("utc", (None, b""))[1]
        utc = utc_bytes.decode("utf-8", errors="ignore").strip()

        image_name, image_content = fields.get("image", (None, b""))

        if not utc or not image_content:
            self._send_html(HTML_FORM.format(result_block="<p style='color:red'>UTC ve fotoğraf zorunlu.</p>"))
            return

        suffix = Path(image_name or "upload.jpg").suffix or ".jpg"
        fd, tmp_path = mkstemp(suffix=suffix)
        try:
            with os.fdopen(fd, "wb") as tmp_file:
                tmp_file.write(image_content)

            try:
                _, result = estimate_from_image_and_utc(tmp_path, utc)
                result_html = (
                    f"<hr><h3>Sonuç</h3>"
                    f"<p><b>Enlem:</b> {'Hesaplanamadı' if result.latitude_deg is None else f'{result.latitude_deg:.5f}°'}</p>"
                    f"<p><b>Boylam:</b> {'Hesaplanamadı' if result.longitude_deg is None else f'{result.longitude_deg:.5f}°'}</p>"
                    f"<p><b>Konum Güveni:</b> {result.location_confidence:.2f}</p>"
                    f"<p><b>Yıldız Eşleşme Skoru:</b> {result.match_confidence:.2f}</p>"
                    f"<p><b>Not:</b> {result.note}</p>"
                )
                if result.matched_stars:
                    stars_html = ''.join(
                        f'<li>{m.name} (RA={m.ra_deg:.2f}, Dec={m.dec_deg:.2f}, skor={m.score:.2f})</li>'
                        for m in result.matched_stars
                    )
                    result_html += f'<p><b>Tanınan yıldızlar:</b></p><ul>{stars_html}</ul>'
            except Exception as exc:
                result_html = f"<p style='color:red'>Hata: {exc}</p>"
        finally:
            try:
                os.remove(tmp_path)
            except OSError:
                pass

        self._send_html(HTML_FORM.format(result_block=result_html))


def run_server(port: int = 8000) -> None:
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"Web arayüz hazır: http://localhost:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
