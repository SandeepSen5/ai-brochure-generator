# AI Brochure Generator

Give it a company website URL and it writes a short brochure for that company, using a **local LLM through [Ollama](https://ollama.com)**. No API keys, and nothing leaves your machine except the page downloads.

## How it works

```
URL -> download landing page -> collect links -> LLM picks the relevant ones
    -> download those pages  -> combine text   -> LLM writes the brochure
    -> stream to terminal    -> save as markdown
```

1. **Scrape** the landing page with `requests` and BeautifulSoup.
2. **Select links**: the model reads all links on the page and returns JSON listing the useful ones (About, Products, Careers...), skipping Privacy, Terms and email links.
3. **Fetch** each selected page.
4. **Write** the brochure: the model gets the combined text and streams the brochure back, which is saved to a markdown file.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- [Ollama](https://ollama.com) running locally, with a model pulled:

```
ollama pull llama3.2
```

## Use Google Gemini instead (free)

1. Get a free key at <https://aistudio.google.com/apikey>.
2. Create a `.env` file in the project root:

```
GEMINI_API_KEY=your-key-here
```

When the key is set, Gemini (`gemini-3.5-flash`) is used instead of Ollama. Override the model with `BROCHURE_MODEL` or `--model`. Free-tier requests are rate limited.

## Web UI

```
uv run brochure-ui
```

Opens a local page where you paste a website URL and get the brochure, with a copy button for the markdown.

## Install

```
git clone <your-repo-url>
cd <repo-folder>
uv sync
```

## Usage

```
uv run brochure-generate https://forthapps.com/in --name "Forth Apps" --output brochure.md
```

| Option | Default | Description |
|---|---|---|
| `url` | required | Company website URL |
| `--name` | the domain | Company name used in the brochure |
| `--model` | `llama3.2` | Any model you have pulled in Ollama |
| `--output` | `brochure.md` | Where to save the markdown brochure |

Progress is printed while it runs. A sample result is in [examples/forth-apps.md](examples/forth-apps.md).

## Project layout

```
src/brochure_generate/
  __init__.py    CLI entry point (argument parsing, saving the file)
  generator.py   link selection and brochure generation (Ollama calls)
  scraper.py     page and link downloading
  prompts.py     system prompts
```

## Notes

- A small model like `llama3.2` (3B) works but may be slow on CPU and can miss details. Larger models (for example `llama3.1:8b` or `qwen2.5:7b`) follow the JSON instructions more reliably.
- Pages that render their content with JavaScript may return little text, because the scraper reads plain HTML.
- Always check the output against the website. Small models can make mistakes.

## Author

**Sandeep Sen** - [LinkedIn](https://www.linkedin.com/in/sandeep-sen-37a643214/)
