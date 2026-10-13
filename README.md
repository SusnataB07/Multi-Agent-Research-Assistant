# Multi-Agent Research Assistant

Four AI agents turn a question into a sourced research report. One agent searches the web, one reads the best source, one writes the report, and one reviews it. You get the draft, a quality score and every link used, all from a Streamlit interface.

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://snta-multi-agent-research-assistant.streamlit.app/)

![App screenshot](screenshot.png)

## How it works

| Step | Agent | What it does |
|------|-------|--------------|
| 1 | Search | Uses Tavily to find up to 3 recent, reliable sources on the topic |
| 2 | Read | Picks the most relevant URL and scrapes its text for deeper content |
| 3 | Write | Drafts a report with an introduction, key findings, conclusions and sources |
| 4 | Critique | Reviews the report and returns a score out of 10, strengths, areas to improve and a one-line verdict |

The Search and Read steps are tool-using LangChain agents. The Write and Critique steps are prompt chains. `pipeline.py` runs the four steps in order and streams progress events to the interface.

## Features

- **Choose your model from the sidebar:** switch between Google Gemini, Groq and Mistral, type any model name your provider supports, and optionally enter an API key right in the app
- Key status indicators showing whether the keys for your chosen provider and for web search are found
- Live pipeline tracker showing each agent's progress and timing
- Critic score with a short verdict, plus total time, word count and source count
- Each report shows which provider and model generated it
- Tabs for the report, critic feedback, sources and raw agent output
- Download the report as `.md` or `.txt`
- History of past runs in the sidebar for the current session
- Command-line mode: run `python pipeline.py` to use the pipeline without the interface

## Tech stack

Python, Streamlit, LangChain, Tavily, BeautifulSoup and Requests, with Gemini, Groq or Mistral models.

## Project structure

```
app.py                  Streamlit interface and sidebar
pipeline.py             Runs the four steps in order and streams progress
agents.py               Model setup, search and reader agents, writer and critic chains
tools.py                Tavily web search and web page scraping tools
requirements.txt        Python dependencies
.streamlit/config.toml  Theme colour
.env.example            Template for your API keys
```

## Setup

You need Python 3.10 or later.

**1. Clone the repo**

```bash
git clone https://github.com/SusnataB07/Multi-Agent-Research-Assistant.git
cd Multi-Agent-Research-Assistant
```

**2. Create and activate a virtual environment**

```bash
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Add your API keys**

Copy `.env.example` to `.env`:

```bash
# Windows (PowerShell)
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Then fill in the keys you have. You need a Tavily key for web search and a key for at least one model provider.

| Provider | Key to set | Default model | Get a key |
|----------|------------|---------------|-----------|
| Google Gemini | `GOOGLE_API_KEY` | `gemini-3.5-flash` | [Google AI Studio](https://aistudio.google.com/apikey) |
| Groq | `GROQ_API_KEY` | `llama-3.3-70b-versatile` | [Groq Console](https://console.groq.com/keys) |
| Mistral | `MISTRAL_API_KEY` | `mistral-small-2506` | [Mistral Console](https://console.mistral.ai) |

`TAVILY_API_KEY` is required for every provider. Get one at [tavily.com](https://tavily.com).

Put each key straight after the `=` with no spaces, quotes or comments on the same line.

## Run

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

## Using the app

1. In the sidebar, pick a **Model provider**. Providers whose key is found show a green dot.
2. Optionally type a different **Model** name. Leave it empty to use the default.
3. Optionally open **API key** and paste a key to use instead of the one in `.env`. It is not saved to disk.
4. Enter a topic and click **Run research**.

`LLM_PROVIDER` and `LLM_MODEL` in `.env` are optional. They set which provider and model are preselected when the app opens, and they are used when you run `python pipeline.py` from the command line.

## Deploy on Streamlit Community Cloud

1. Push this repo to GitHub, making sure `.env` is not committed.
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with GitHub, and create an app from this repo with `main` as the branch and `app.py` as the main file.
3. In **Advanced settings**, choose Python 3.11 or 3.12 and paste your keys into **Secrets** in TOML format, with quotes around each value:

```toml
GOOGLE_API_KEY = "your_key"
GROQ_API_KEY = "your_key"
MISTRAL_API_KEY = "your_key"
TAVILY_API_KEY = "your_key"
```

4. Click **Deploy**. Pushing new commits to `main` redeploys the app automatically.

Keys in Secrets are used by every visitor, so use free-tier keys for a public demo and keep an eye on your usage.

## Troubleshooting

- **A provider shows a green dot but fails to run:** the dot only means a value was found, not that the key is valid. Check the key, and make sure no comment such as `# groq` follows the `=` in `.env`, because that text would be read as the key.
- **"Could not load the pipeline or agents: Missing API key":** the key for the selected provider is not set. Add it to `.env`, to Secrets, or paste it in the sidebar.
- **Search fails:** check that `TAVILY_API_KEY` is set and that you have credits left.
- **Rate limit or quota error:** wait a minute and retry, or pick another provider in the sidebar.
- **Model not found:** the default model may have been retired or renamed. Type a current model name in the sidebar's Model box.
- **Changes to `.env` not picked up:** stop Streamlit and run it again, since the file is read at startup.
- **Some pages return no content:** the reader agent can only scrape pages that allow it, and it reads the first 3,000 characters of the page it picks.

## Notes

Never commit your `.env` file. It is listed in `.gitignore` so your keys stay local.
