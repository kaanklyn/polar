# Polar Offline Star Navigation Prototype

Bu proje, GPS ve internet olmadan yıldız gözlemleriyle konum tahmini yapmaya yönelik bir prototiptir.

## Bu proje ne yapıyor?

Bu bir **mobil uygulama değil**, mobil uygulamanın içinde çalışacak astronomi hesabının bilgisayarda test edilen ilk sürümüdür.

- Manuel olarak girilen yıldız verilerinden enlem-boylam tahmini yapar.
- Offline çalışır (internet gerekmez).
- Komut satırından çalışır.

---

## Hiç kodlama bilmiyorsan: adım adım çalıştırma

Aşağıdaki adımları sırayla yapman yeterli.

## 1) Bilgisayarına Python kur

- [https://www.python.org/downloads/](https://www.python.org/downloads/) adresine git.
- İşletim sistemine uygun sürümü indir.
- Kurarken **"Add Python to PATH"** kutucuğunu mutlaka işaretle (Windows için önemli).

Kurulum tamamlandıktan sonra terminalde kontrol et:

```bash
python --version
```

veya bazı sistemlerde:

```bash
python3 --version
```

Sürüm görüyorsan tamam.

## 2) Proje klasörünü aç

Bu dosyaların olduğu klasöre girmen gerekiyor (`README.md`, `app.py`, `astronomy.py` aynı yerde olmalı).

Terminalde örnek:

```bash
cd proje_klasoru
```

## 3) Programı çalıştır

Aşağıdaki komutu **tek satır** olarak kopyalayıp çalıştır:

```bash
python app.py --utc "2026-01-15T22:30:00Z" --polaris-alt 72.1 --star-ra 88.7929 --star-dec 7.4071 --star-alt 34.2 --star-az 140.0
```

Eğer `python` çalışmazsa `python3` ile dene:

```bash
python3 app.py --utc "2026-01-15T22:30:00Z" --polaris-alt 72.1 --star-ra 88.7929 --star-dec 7.4071 --star-alt 34.2 --star-az 140.0
```

Beklenen çıktı benzeri:

- Enlem: `72.x`
- Boylam: `...`
- Güven: `0.80`

## 4) Testleri çalıştır (zorunlu değil ama önerilir)

```bash
python -m unittest -v
```

veya

```bash
python3 -m unittest -v
```

---

## Parametreler (kısa açıklama)

- `--utc`: Ölçüm zamanı (UTC), örn: `2026-01-15T22:30:00Z`
- `--polaris-alt`: Kutup Yıldızı yüksekliği (derece)
- `--star-ra`: Referans yıldızın Right Ascension değeri (derece)
- `--star-dec`: Referans yıldızın Declination değeri (derece)
- `--star-alt`: Referans yıldızın gözlenen yüksekliği (derece)
- `--star-az`: Referans yıldızın azimutu (derece, kuzey=0, doğu=90)

---

## Sık görülen hatalar

- **`python is not recognized`**: Python kurulu değil veya PATH'e eklenmedi.
- **`No such file or directory: app.py`**: Terminalde doğru klasörde değilsin.
- **`ModuleNotFoundError`**: Dosyalar eksik veya farklı klasörde.

---

## Sonraki adım (istersen)

İstersen bir sonraki aşamada sana şunları da hazırlayabilirim:

- Görsel arayüzlü (butonlu) basit sürüm
- Telefonda çalıştırılabilir hale getirme planı
- Kamera görüntüsünden otomatik yıldız noktası çıkarma
