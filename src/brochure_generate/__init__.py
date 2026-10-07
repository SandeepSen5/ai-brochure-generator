import argparse
from urllib.parse import urlparse

from .generator import DEFAULT_MODEL, create_brochure


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a company brochure from a website URL using Ollama.")
    parser.add_argument("url", help="Company website URL, e.g. https://example.com")
    parser.add_argument("--name", help="Company name (defaults to the domain)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Ollama model (default: {DEFAULT_MODEL})")
    parser.add_argument("--output", default="brochure.md", help="Output markdown file")
    args = parser.parse_args()

    url = args.url if args.url.startswith("http") else "https://" + args.url
    name = args.name or urlparse(url).netloc.removeprefix("www.")

    parts = []
    for text in create_brochure(name, url, args.model):
        print(text, end="", flush=True)
        parts.append(text)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write("".join(parts))
    print(f"\n\nSaved to {args.output}")
