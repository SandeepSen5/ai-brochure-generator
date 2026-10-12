import argparse
import sys
from urllib.parse import urlparse

import openai
import requests

from .generator import DEFAULT_MODEL, USING_GEMINI, create_brochure


def main() -> None:
    # Windows consoles default to cp1252, which can't print symbols like the rupee sign.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Generate a company brochure from a website URL using Gemini (free API key) or a local Ollama model.")
    parser.add_argument("url", help="Company website URL, e.g. https://example.com")
    parser.add_argument("--name", help="Company name (defaults to the domain)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model name (default: {DEFAULT_MODEL})")
    parser.add_argument("--output", default="brochure.md", help="Output markdown file")
    args = parser.parse_args()

    url = args.url if args.url.startswith("http") else "https://" + args.url
    name = args.name or urlparse(url).netloc.removeprefix("www.")

    parts = []
    try:
        for text in create_brochure(name, url, args.model):
            print(text, end="", flush=True)
            parts.append(text)
    except requests.RequestException as e:
        sys.exit(f"Could not fetch the website {url}: {e}")
    except openai.AuthenticationError:
        sys.exit("The Gemini API key was rejected. Check GEMINI_API_KEY.")
    except openai.RateLimitError:
        sys.exit("Rate limit hit on the free tier. Wait a minute and try again.")
    except openai.InternalServerError:
        sys.exit("The model service is overloaded right now. Try again in a minute.")
    except openai.APIConnectionError:
        if USING_GEMINI:
            sys.exit("Could not reach the Gemini API. Check your internet connection.")
        sys.exit("Could not reach Ollama. Make sure it is running (check: curl.exe http://localhost:11434).")
    except openai.NotFoundError:
        if USING_GEMINI:
            sys.exit(f"Model '{args.model}' not available on Gemini. Try --model gemini-3.5-flash.")
        sys.exit(f"Model '{args.model}' not found. Pull it first: ollama pull {args.model}")
    with open(args.output, "w", encoding="utf-8") as f:
        f.write("".join(parts))
    print(f"\n\nSaved to {args.output}")
