import gradio as gr
import openai
import requests

from .generator import DEFAULT_MODEL, USING_GEMINI, create_brochure

PROVIDER = f"Gemini ({DEFAULT_MODEL})" if USING_GEMINI else f"Ollama ({DEFAULT_MODEL})"


def generate(company_name, url):
    url = (url or "").strip()
    if not url:
        raise gr.Error("Please paste a website URL.")
    if not url.startswith("http"):
        url = "https://" + url
    text = ""
    try:
        for chunk in create_brochure(company_name.strip() or url, url):
            text += chunk
            yield text
    except requests.RequestException as e:
        raise gr.Error(f"Could not fetch {url}: {e}")
    except openai.AuthenticationError:
        raise gr.Error("API key rejected. Check GEMINI_API_KEY.")
    except openai.RateLimitError:
        raise gr.Error("Free-tier rate limit hit. Wait a minute and try again.")
    except openai.InternalServerError:
        raise gr.Error("The model service is overloaded right now. Try again in a minute.")
    except openai.APIConnectionError:
        raise gr.Error("Could not reach the model API.")


def build_app():
    with gr.Blocks(title="Brochure Generator") as app:
        gr.Markdown(f"# Company Brochure Generator\nPowered by **{PROVIDER}**.")
        with gr.Row():
            name = gr.Textbox(label="Company name (optional)", scale=1)
            url = gr.Textbox(label="Website URL", placeholder="https://example.com", scale=3)
        button = gr.Button("Generate brochure", variant="primary")
        preview = gr.Markdown(label="Brochure")
        raw = gr.Textbox(label="Markdown (copy from here)", lines=12, buttons=["copy"])

        event = button.click(generate, [name, url], preview)
        event.then(lambda t: t, preview, raw)
        url.submit(generate, [name, url], preview).then(lambda t: t, preview, raw)
    return app


def main() -> None:
    build_app().launch()
