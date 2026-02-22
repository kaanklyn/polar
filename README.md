# Polar Offline Star Navigation Prototype

Bu proje, GPS ve internet olmadan yıldız gözlemleriyle konum tahmini yapmaya yönelik bir prototiptir.

## Yeni: Fotoğraftan yıldız okuma (MVP)

Artık uygulama `--image` parametresi ile gökyüzü fotoğrafından parlak yıldız noktalarını otomatik çıkarmaya çalışır.

> Bu sürüm hâlâ MVP'dir: Yıldızın kimliğini (RA/Dec) otomatik tanımaz, referans yıldızın `--star-ra` ve `--star-dec` bilgisi kullanıcıdan alınır.

## 1) Kurulum

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pillow
```

## 2) Manuel kullanım (fotoğrafsız)

```bash
python3 app.py --utc "2026-01-15T22:30:00Z" --polaris-alt 72.1 --star-ra 88.7929 --star-dec 7.4071 --star-alt 34.2 --star-az 140.0
```

## 3) Fotoğraflı kullanım

```bash
python3 app.py \
  --utc "2026-01-15T22:30:00Z" \
  --image "sample_sky.jpg" \
  --star-ra 88.7929 \
  --star-dec 7.4071 \
  --camera-az 0 \
  --camera-alt 45 \
  --hfov 60 \
  --vfov 40
```

Fotoğraflı modda:
- En parlak yıldız referans yıldız ölçümü için kullanılır (`star-alt`, `star-az` otomatikleşir).
- `--polaris-alt` verilmezse, görüntüde en üstteki parlak nokta Polaris yaklaşımı için kullanılır.

## Parametreler

- `--utc`: ISO-8601 UTC zamanı
- `--star-ra`, `--star-dec`: Referans yıldızın katalog değeri (derece)
- `--polaris-alt`: (opsiyonel) Polaris yüksekliği
- `--star-alt`, `--star-az`: (opsiyonel, manuel modda gerekli)
- `--image`: Gökyüzü fotoğrafı
- `--camera-az`: Kameranın baktığı azimut
- `--camera-alt`: Kameranın baktığı yükseklik
- `--hfov`, `--vfov`: Kamera görüş açıları

## Test

```bash
python3 -m unittest -v
```
