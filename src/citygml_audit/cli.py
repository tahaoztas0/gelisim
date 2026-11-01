"""Command line interface for CityGML Audit."""
import argparse
import json
import sys
from pathlib import Path

from .validator import audit_file


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Check basic CityGML geometry and XML structure.")
    parser.add_argument("path", help="A CityGML/GML/XML file or a directory")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON results")
    parser.add_argument("--dimension", type=int, choices=[2, 3], default=3)
    parser.add_argument("--tolerance", type=float, default=0.01, help="Allowed planar deviation in coordinate units")
    parser.add_argument("--fail-on-warning", action="store_true")
    args = parser.parse_args(argv)
    if not 0 <= args.tolerance < float("inf"):
        parser.error("--tolerance must be finite and nonnegative")
    path = Path(args.path)
    if not path.exists():
        parser.error(f"Path not found: {path}")
    files = sorted(p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in (".xml", ".gml")) if path.is_dir() else [path]
    if not files:
        parser.error("No .gml or .xml files found")
    results = []
    for file in files:
        try:
            results.append(audit_file(file, dimension=args.dimension, tolerance=args.tolerance))
        except (OSError, UnicodeError) as exc:
            results.append({"file": str(file), "buildings": 0, "polygons": 0, "rings": 0,
                            "findings": [{"severity": "error", "code": "READ_ERROR", "message": str(exc), "feature": ""}]})
    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        for result in results:
            print(f"{result['file']}: {result['buildings']} buildings, {result['polygons']} polygons, {result['rings']} rings")
            for item in result["findings"]:
                print(f"  {item['severity'].upper()} [{item['code']}] {item['feature']} {item['message']}")
            if not result["findings"]:
                print("  No findings")
    return int(any(item["severity"] == "error" or (args.fail_on_warning and item["severity"] == "warning")
                   for result in results for item in result["findings"]))


if __name__ == "__main__":
    sys.exit(main())
