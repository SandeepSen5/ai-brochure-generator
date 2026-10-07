import json
from urllib.parse import urljoin

from openai import OpenAI

from .prompts import BROCHURE_SYSTEM_PROMPT, LINK_SYSTEM_PROMPT
from .scraper import fetch_website_contents, fetch_website_links

OLLAMA_BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODEL = "llama3.2"

# Ollama exposes an OpenAI-compatible API; the key is required by the client but ignored.
client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")


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
    links = list(dict.fromkeys(urljoin(url, link) for link in fetch_website_links(url)))
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
    return [
        item for item in selected
        if isinstance(item, dict) and str(item.get("url", "")).startswith("http")
    ]


def fetch_page_and_all_relevant_links(url, model=DEFAULT_MODEL):
    """Collect the landing page plus the contents of every relevant linked page."""
    result = "## Landing Page:\n\n" + fetch_website_contents(url)
    result += "\n\n## Relevant Links:\n"
    for link in select_relevant_links(url, model):
        result += f"\n\n### Link: {link.get('type', 'page')}\n"
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
    # Cap the context so a small local model isn't overwhelmed.
    user_prompt += fetch_page_and_all_relevant_links(url, model)[:5_000]

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
