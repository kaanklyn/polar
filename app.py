import argparse
from astronomy import estimate_location, parse_utc
from vision import detect_star_points, pixel_to_alt_az


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Offline yıldız tabanlı konum tahmini")
    p.add_argument("--utc", required=True, help="ISO-8601 UTC, örn: 2026-01-15T22:30:00Z")
    p.add_argument("--polaris-alt", required=True, type=float, help="Polaris yüksekliği (derece)")
    p.add_argument("--star-ra", required=True, type=float, help="Referans yıldız RA (derece)")
    p.add_argument("--star-dec", required=True, type=float, help="Referans yıldız Dec (derece)")
    p.add_argument("--star-alt", type=float, help="Referans yıldız yüksekliği (derece)")
    p.add_argument("--star-az", type=float, help="Referans yıldız azimutu (derece)")
    p.add_argument("--image", help="Gökyüzü fotoğrafı yolu (opsiyonel)")
    p.add_argument("--camera-az", type=float, default=0.0, help="Kamera bakış azimutu (derece)")
    p.add_argument("--camera-alt", type=float, default=45.0, help="Kamera bakış yüksekliği (derece)")
    p.add_argument("--hfov", type=float, default=60.0, help="Kamera yatay görüş açısı")
    p.add_argument("--vfov", type=float, default=40.0, help="Kamera dikey görüş açısı")
    return p


def main() -> None:
    args = build_parser().parse_args()
    utc = parse_utc(args.utc)

    star_alt = args.star_alt
    star_az = args.star_az
    polaris_alt = args.polaris_alt

    if args.image:
        width, height, stars = detect_star_points(args.image)
        if not stars:
            raise SystemExit("Fotoğrafta yeterli parlak yıldız noktası bulunamadı.")

        ref = stars[0]
        star_alt, star_az = pixel_to_alt_az(
            ref.x, ref.y, width, height, args.camera_az, args.camera_alt, args.hfov, args.vfov
        )

        if polaris_alt is None:
            highest = min(stars, key=lambda s: s.y)
            polaris_alt, _ = pixel_to_alt_az(
                highest.x, highest.y, width, height, args.camera_az, args.camera_alt, args.hfov, args.vfov
            )

    if polaris_alt is None or star_alt is None or star_az is None:
        raise SystemExit("Manuel mod için --polaris-alt --star-alt --star-az gerekli; veya --image ile otomatik ölçüm kullan.")

    result = estimate_location(
        utc_dt=utc,
        polaris_alt_deg=polaris_alt,
        star_ra_deg=args.star_ra,
        star_dec_deg=args.star_dec,
        star_alt_deg=star_alt,
        star_az_deg=star_az,
    )

    print(f"Enlem  : {result.latitude_deg:.5f}°")
    print(f"Boylam : {result.longitude_deg:.5f}°")
    print(f"Güven  : {result.confidence:.2f}")


if __name__ == "__main__":
    main()
