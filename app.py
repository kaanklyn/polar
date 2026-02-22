import argparse

from pipeline import estimate_from_image_and_utc


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Fotoğraf + tarih ile yıldız tabanlı konum (MVP)")
    p.add_argument("--utc", required=True, help="ISO-8601 UTC, örn: 2026-01-15T22:30:00Z")
    p.add_argument("--image", required=True, help="Gökyüzü fotoğrafı yolu")
    return p


def main() -> None:
    args = build_parser().parse_args()
    _, result = estimate_from_image_and_utc(args.image, args.utc)

    if result.latitude_deg is None:
        print("Enlem  : Hesaplanamadı")
    else:
        print(f"Enlem  : {result.latitude_deg:.5f}°")

    if result.longitude_deg is None:
        print("Boylam : Hesaplanamadı")
    else:
        print(f"Boylam : {result.longitude_deg:.5f}°")

    print(f"Güven  : {result.confidence:.2f}")
    print(f"Not    : {result.note}")


if __name__ == "__main__":
    main()
