uv init --package   --package gives you src/brochure_generator/, a proper package layout, plus pyproject.toml, .gitignore and a git repo.


uv add openai requests beautifulsoup4 python-dotenv
uv add --dev pytest

Features to add after the first push:

Progress messages while it runs
HTML or PDF output
A Gradio web UI
Tests with pytest, since it's already a dev dependency