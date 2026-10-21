import argparse
import sys
from pathlib import Path

from app.config.logging_config import setup_logging
from app.generator import Generator

setup_logging()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a FastAPI project from a YAML spec."
    )
    parser.add_argument("--spec", "-s", required=True, help="Path to YAML spec file")
    parser.add_argument("--output", "-o", required=True, help="Output directory")
    parser.add_argument(
        "--force", "-f", action="store_true", help="Overwrite existing output"
    )
    args = parser.parse_args()

    spec_path = Path(args.spec)
    output_path = Path(args.output)

    if not spec_path.exists():
        print(f"Error: spec file not found: {spec_path}", file=sys.stderr)
        sys.exit(1)

    if output_path.exists() and not args.force:
        print(
            f"Error: output directory '{output_path}' exists. \
            Use --force to overwrite.",
            file=sys.stderr,
        )
        sys.exit(1)

    generator = Generator(spec_path)
    spec = generator.load_spec()
    generator.custom_logger.info(f"Loaded spec: {spec.name}")
    created = generator.generate(spec, output_path)

    generator.custom_logger.info(f"\nGenerated {len(created)} files:\n")
    for p in created:
        generator.custom_logger.info(f"  ✓ {p.relative_to(output_path)}")

    generator.custom_logger.info(f"\nDone! → {output_path.resolve()}")
    generator.custom_logger.info("\nNext steps:")
    generator.custom_logger.info(f"  cd {output_path}")
    generator.custom_logger.info("  pip install -r requirements.txt")
    generator.custom_logger.info("  pytest")


if __name__ == "__main__":
    main()
