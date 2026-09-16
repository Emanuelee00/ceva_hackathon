# CEVA Hackathon — FVL Transport Analysis

Interactive agentic dashboard for the FVL transport dataset: a local LLM
(via Ollama + LangGraph) routes natural-language questions to a fixed set of
verified analysis tools, plus a dispatcher form that alerts when a truck is
assigned a Loading Factor well below its own historical maximum.

## Setup

```bash
make agent
```

Pulls `qwen2.5:3b-instruct` if needed (first run only, ~2GB, needs internet —
do this well ahead of a live demo), starts Ollama, and launches the
Streamlit app at http://localhost:8501. Two tabs: **Dispatcher check** (the
loading-factor alert form) and **Ask the data** (chat over the other 5
analyses: empty-km cost, backhaul matching, geo mismatch, fleet
concentration, delivery delays).

The LLM only ever picks a tool name (constrained JSON-schema decoding, see
`agent/`) — it never computes or narrates numbers itself; every number and
every answer sentence comes from deterministic Python (`agent/tools.py`'s
`narrate()`), so nothing shown can be invented by the model.

Other useful commands:

```bash
make run   # analyze.py sanity checks (empty km, loading factor, dates)
make cost  # translate empty km into euros/CO2 (declared assumptions)
```

To use a different file:

```bash
uv run python analyze.py path/to/file.csv
```

## Data

```
data/
  xlsx/   raw Excel originals
  csv/    converted CSVs (one per sheet)
```

Put new Excel files in `data/xlsx/` and run `make convert` to turn every
sheet into a CSV under `data/csv/`. See [CONTEXT.md](CONTEXT.md) for the
full context and known datasets.
