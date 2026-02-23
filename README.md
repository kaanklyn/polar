# Polar Offline Star Navigation Prototype

Bu sürüm hızlı geliştirme için **yıldız tanıma (star matching)** adımını koda ekler.

## Şu an ne yapıyor?

- Fotoğraftan parlak yıldız noktalarını bulur.
- Dahili parlak yıldız kataloğu ile üçgen oranları üzerinden yıldız tanımayı dener.
- Eşleşen yıldız isimlerini listeler.
- Yıldız eşleşmesi yeterliyse yaklaşık lat/lon üretir (Stellarium odaklı hızlı solver).

## Kurulum

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pillow
```

## CLI kullanım

```bash
python3 app.py --utc "2026-01-15T22:30:00Z" --image "sample_sky.jpg"
```

## Web arayüz

```bash
python3 web_ui.py
```

Aç: `http://localhost:8000`

## Test

```bash
python3 -m unittest -v
```


## Katalogı güvenilir kaynaktan güncelleme

Aşağıdaki komut internetten HYG veri setini indirir, parlak yıldız alt kümesini üretir ve dosyaları günceller:

```bash
python3 scripts/update_catalog.py
```

Üretilen dosyalar:
- `data/bright_stars.csv`
- `data/bright_stars.source.json` (kaynak URL, indirme zamanı, checksum)


Not: `Konum Güveni` ile `Ön Eşleşme Skoru` farklıdır. Solver tamamlanana kadar konum güveni 0.00 olur.


## Solver varsayımları (önemli)

- Bu sürüm Stellarium ekran görüntülerine göre kalibre edilmiş hızlı bir yaklaşımdır.
- Kamera merkezinin zenith'e yakın olduğu varsayılır.
- Sonuçlar yaklaşık değerdir; saha kullanımından önce gerçek veriyle kalibrasyon gerekir.
