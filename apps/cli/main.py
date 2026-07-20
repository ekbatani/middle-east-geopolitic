import argparse
import sys

import httpx

API_BASE_URL_DEFAULT = "http://localhost:8000"


def cmd_version(_: argparse.Namespace) -> int:
    print("mei 0.1.0")
    return 0


def cmd_health(args: argparse.Namespace) -> int:
    """Ping the API's liveness endpoint. Useful for local smoke-testing the stack."""
    try:
        response = httpx.get(f"{args.api_url}/health/live", timeout=5)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        print(f"API unreachable at {args.api_url}: {exc}", file=sys.stderr)
        return 1
    print(response.json())
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mei", description="Middle East Geopolitical Intelligence Platform CLI"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    version_parser = subparsers.add_parser("version", help="Print the CLI version")
    version_parser.set_defaults(func=cmd_version)

    health_parser = subparsers.add_parser("health", help="Check API liveness")
    health_parser.add_argument("--api-url", default=API_BASE_URL_DEFAULT)
    health_parser.set_defaults(func=cmd_health)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
