# CityGML Audit

[![CI](https://github.com/tahaoztas0/gelisim/actions/workflows/ci.yml/badge.svg)](https://github.com/tahaoztas0/gelisim/actions/workflows/ci.yml)

**Open-source, dependency-free quality checks for CityGML building geometry.**

CityGML Audit is an early-stage Python command-line tool for reviewing CityGML (GML/XML) building files before exchange or publication. It checks basic XML structure and supported GML polygon rings, then produces human-readable or machine-readable findings.

> **Project status:** v0.1.0 starter release. This project is new; it does not claim established adoption or standards certification.

## What it checks

- XML well-formedness, empty models and duplicate `gml:id` attributes
- Building and polygon counts
- LinearRing coordinate readability and finite coordinates
- Closed rings, minimum distinct vertices and non-degenerate geometry
- Non-planar 3D rings within configurable tolerance

**Scope:** Basic structural and geometry checks, not complete OGC schema validation, coordinate-system verification, CityGML semantic validation, or proof of cadastral/legal conformity. Supports `gml:posList`, `gml:pos`, and legacy `gml:coordinates`; curved surfaces and external geometry references are not resolved.

## Installation

Requires Python 3.10 or newer.

```bash
python -m pip install -e .
```

## Usage

```bash
citygml-audit examples/valid_building.gml
citygml-audit path/to/citygml-files --json
citygml-audit model.gml --dimension 3 --tolerance 0.01 --fail-on-warning
python -m citygml_audit --help
```

When a directory is supplied, `.gml` and `.xml` files are inspected recursively. The CLI exits with **0** when no findings requiring failure are found, **1** when errors (or warnings with `--fail-on-warning`) exist, and **2** for invocation/input errors.

## Development

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

See [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), and [ROADMAP.md](ROADMAP.md).

## Contributing

Bug reports, reproducible CityGML test cases, documentation improvements and code contributions are welcome. Do not submit private architectural drawings or cadastral data without permission.

## License

MIT License — see [LICENSE](LICENSE). The project is independently maintained and is not affiliated with OGC or OpenAI.
