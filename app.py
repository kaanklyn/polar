import argparse

from pipeline import estimate_from_image_and_utc


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Fotoğraf + tarih ile yıldız tanıma (hızlı MVP)")
    p.add_argument("--utc", required=True, help="ISO-8601 UTC, örn: 2026-01-15T22:30:00Z")
    p.add_argument("--image", required=True, help="Gökyüzü fotoğrafı yolu")
    return p


def main() -> None:
    args = build_parser().parse_args()
    _, result = estimate_from_image_and_utc(args.image, args.utc)

    print("Enlem  : Hesaplanamadı")
    print("Boylam : Hesaplanamadı")
    print(f"Güven  : {result.confidence:.2f}")
    print(f"Not    : {result.note}")

    if result.matched_stars:
        print("\nEşleşen yıldızlar:")
        for m in result.matched_stars:
            print(f"- {m.name} (RA={m.ra_deg:.3f}, Dec={m.dec_deg:.3f}, skor={m.score:.2f})")


if __name__ == "__main__":
    main()
