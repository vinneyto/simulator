from __future__ import annotations

import argparse
import json
from pathlib import Path

from simulator.api import create_app


def export_schema(destination: Path) -> None:
    destination.write_text(
        json.dumps(create_app().openapi(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def run() -> None:
    parser = argparse.ArgumentParser(description="Export the generated Simulator OpenAPI schema")
    parser.add_argument("destination", nargs="?", type=Path, default=Path("openapi.json"))
    args = parser.parse_args()
    export_schema(args.destination)


if __name__ == "__main__":
    run()
