import argparse
from astronomy import estimate_location, parse_utc


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Offline yıldız tabanlı konum tahmini")
    p.add_argument("--utc", required=True, help="ISO-8601 UTC, örn: 2026-01-15T22:30:00Z")
    p.add_argument("--polaris-alt", required=True, type=float, help="Polaris yüksekliği (derece)")
    p.add_argument("--star-ra", required=True, type=float, help="Referans yıldız RA (derece)")
    p.add_argument("--star-dec", required=True, type=float, help="Referans yıldız Dec (derece)")
    p.add_argument("--star-alt", required=True, type=float, help="Referans yıldız yüksekliği (derece)")
    p.add_argument("--star-az", required=True, type=float, help="Referans yıldız azimutu (derece)")
    return p


def main() -> None:
    args = build_parser().parse_args()
    utc = parse_utc(args.utc)

    result = estimate_location(
        utc_dt=utc,
        polaris_alt_deg=args.polaris_alt,
        star_ra_deg=args.star_ra,
        star_dec_deg=args.star_dec,
        star_alt_deg=args.star_alt,
        star_az_deg=args.star_az,
    )

    print(f"Enlem  : {result.latitude_deg:.5f}°")
    print(f"Boylam : {result.longitude_deg:.5f}°")
    print(f"Güven  : {result.confidence:.2f}")


if __name__ == "__main__":
    main()
