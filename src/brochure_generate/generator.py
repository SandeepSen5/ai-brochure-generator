import json
import os
import sys
from urllib.parse import urljoin

from dotenv import load_dotenv
from openai import OpenAI

from .prompts import BROCHURE_SYSTEM_PROMPT, LINK_SYSTEM_PROMPT
from .scraper import fetch_website_contents, fetch_website_links

load_dotenv()

OLLAMA_BASE_URL = "http://localhost:11434/v1"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

# Both Gemini and Ollama expose OpenAI-compatible APIs. If GEMINI_API_KEY is set
# (free key from https://aistudio.google.com/apikey) use Gemini, otherwise local Ollama.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
USING_GEMINI = bool(GEMINI_API_KEY)

if USING_GEMINI:
    DEFAULT_MODEL = os.environ.get("BROCHURE_MODEL", "gemini-3.5-flash")
    # The free tier is busy at times; retry 429/503 with backoff.
    client = OpenAI(base_url=GEMINI_BASE_URL, api_key=GEMINI_API_KEY, max_retries=6)
    MAX_CONTEXT_CHARS = 20_000
else:
    DEFAULT_MODEL = os.environ.get("BROCHURE_MODEL", "llama3.2")
    # The key is required by the client but ignored by Ollama.
    client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
    MAX_CONTEXT_CHARS = 5_000  # keep small local models from being overwhelmed


def log(message):
    """Progress messages go to stderr so they don't mix with the brochure text."""
    print(message, file=sys.stderr, flush=True)


def get_links_user_prompt(url, links):
    user_prompt = f"Here is the list of links on the website {url} - "
    user_prompt += "please decide which of these are relevant web links for a brochure about the company. "
    user_prompt += "Respond with the full https URL in JSON format. Do not include Terms of Service, Privacy, email links.\n"
    user_prompt += "Links (some might be relative links):\n"
    user_prompt += "\n".join(links)
    return user_prompt


def select_relevant_links(url, model=DEFAULT_MODEL):
    """Ask the LLM which links on the page are worth including in the brochure."""
    # Resolve relative links up front so the model (and we) only deal with absolute URLs.
    log("Collecting links from the landing page...")
    links = list(dict.fromkeys(urljoin(url, link) for link in fetch_website_links(url)))
    log(f"Found {len(links)} links. Asking {model} to pick the relevant ones...")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": LINK_SYSTEM_PROMPT},
            {"role": "user", "content": get_links_user_prompt(url, links)},
        ],
        response_format={"type": "json_object"},
    )
    try:
        selected = json.loads(response.choices[0].message.content).get("links", [])
    except json.JSONDecodeError:
        return []
    selected = [
        item for item in selected
        if isinstance(item, dict) and str(item.get("url", "")).startswith("http")
    ]
    log(f"Selected {len(selected)} relevant links.")
    return selected


def fetch_page_and_all_relevant_links(url, model=DEFAULT_MODEL):
    """Collect the landing page plus the contents of every relevant linked page."""
    result = "## Landing Page:\n\n" + fetch_website_contents(url)
    result += "\n\n## Relevant Links:\n"
    for link in select_relevant_links(url, model):
        result += f"\n\n### Link: {link.get('type', 'page')}\n"
        log(f"Fetching {link.get('type', 'page')}: {link['url']}")
        try:
            result += fetch_website_contents(link["url"])
        except Exception as e:  # one dead link shouldn't kill the brochure
            result += f"(could not fetch {link['url']}: {e})"
    return result


def create_brochure(company_name, url, model=DEFAULT_MODEL):
    """Generate the brochure markdown, streaming chunks as they arrive."""
    user_prompt = f"You are looking at a company called: {company_name}\n"
    user_prompt += "Here are the contents of its landing page and other relevant pages; "
    user_prompt += "use this information to build a short brochure of the company in markdown without code blocks.\n\n"
    user_prompt += fetch_page_and_all_relevant_links(url, model)[:MAX_CONTEXT_CHARS]

    log("Writing the brochure...\n")
    stream = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": BROCHURE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        stream=True,
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
