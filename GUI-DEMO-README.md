# GUI Demo Bundle

Copy/unzip this bundle into the repository root.

It adds:

- `ui/streamlit_app.py`
- `scripts/setup-gui-demo.sh`
- `scripts/demo-local.sh`
- `scripts/demo-stop.sh`

The setup script adds `streamlit` to `requirements.txt` if it is not already present.

## One-time setup

```bash
./scripts/setup-gui-demo.sh
```

## Run Gemini demo

```bash
./scripts/demo-local.sh gemini
```

## Run Gemma/Ollama demo

```bash
./scripts/demo-local.sh gemma
```

## Stop

```bash
./scripts/demo-stop.sh
```

The GUI opens at:

```text
http://localhost:8501
```

The model is selected before the Python process starts. This is intentional because the
current Google ADK agents resolve their model during module import. The GUI therefore
shows the active model rather than pretending that an in-page dropdown can safely hot-swap it.

## v0.9 behavior

The same UI is used for Gemini and Gemma/Ollama. Houston pediatric dentistry is an acceptance example, not application configuration. The UI exposes Grounded Answer, Search Plan, Evidence, Citations, Transparency, and complete research output. Provider results are evidence-supported candidates, not a claim that NPPES proves who is “best”.
