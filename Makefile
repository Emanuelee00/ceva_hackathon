.PHONY: all run cost convert sync ollama-serve ollama-pull agent

sync:
	uv sync

convert: sync
	uv run python convert_xlsx.py

run: sync
	uv run python analyze.py

cost: sync
	uv run python cost_estimate.py

ollama-serve:
	@if curl -s -o /dev/null http://localhost:11434/; then \
		echo "Ollama already running"; \
	else \
		nohup ollama serve > /tmp/ollama.log 2>&1 & disown; \
		sleep 2; \
	fi

ollama-pull: ollama-serve
	@ollama list | grep -q qwen2.5:3b-instruct || ollama pull qwen2.5:3b-instruct

agent: sync ollama-pull
	uv run streamlit run app.py

all: convert run cost agent
