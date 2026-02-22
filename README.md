# Polar Offline Star Navigation Prototype

İstediğin sade kullanım bu sürümde hazır:

- Sadece **fotoğraf yükle**
- Sadece **tarih/saat (UTC) gir**
- Telefonun arka kamerası gökyüzüne bakıyor kabulü sabit (MVP)

## Ne değişti?

Bu sürümde kullanıcıdan başka teknik parametre istenmez.

> Not: Bu sade modda güvenilir şekilde yalnızca **enlem** tahmini yapılır.
> Boylam için yıldız kimlik eşlemesi (star matching) gerekir; sonraki adımda eklenebilir.

## 1) Kurulum

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pillow
```

## 2) Web arayüzü ile çalıştır (önerilen)

```bash
python3 web_ui.py
```

Tarayıcıdan aç:

- `http://localhost:8000`

Formda sadece:
- `UTC tarih/saat`
- `fotoğraf`

girip **Hesapla** butonuna bas.

## 3) Komut satırı alternatifi

```bash
python3 app.py --utc "2026-01-15T22:30:00Z" --image "sample_sky.jpg"
```

## 4) Test

```bash
python3 -m unittest -v
```


## Not

- `web_ui.py` Python 3.13+ ile uyumludur (`cgi` modülü kullanılmaz).
