"""Ollama-backed router LLM. Uses schema-constrained JSON output (Ollama's
native structured-output support) at temperature 0 for determinism — this is
the only LLM call in the pipeline; answer text is templated deterministically
in agent/tools.py (a 3B model was unreliable at freely narrating numbers).
"""

from langchain_ollama import ChatOllama

from agent.schema import RouterDecision
from agent.tools import TOOL_DESCRIPTIONS

MODEL = "qwen2.5:1.5b-instruct"  # switched down from 3b: this machine ran out of
# memory for the 3b model mid-hackathon (system under memory pressure from many
# other open processes); the 1.5b model needs roughly half the RAM. Re-test
# router accuracy if you revert this once more memory is free.


ROUTER_EXAMPLES = [
    ("how much fuel do we waste on empty trips?", "empty_km_cost"),
    ("quanto ci costano i chilometri a vuoto?", "empty_km_cost"),
    ("what's the capital of France?", "out_of_scope"),
    ("tell me a joke", "out_of_scope"),
    ("raccontami una barzelletta", "out_of_scope"),
    ("what's the weather like today?", "out_of_scope"),
]


def router_prompt(question: str) -> str:
    tools = "\n".join(f"- {name}: {desc}" for name, desc in TOOL_DESCRIPTIONS.items())
    examples = "\n".join(f'Q: "{q}" -> {t}' for q, t in ROUTER_EXAMPLES)
    return (
        "You are a router for a French vehicle-transport (FVL) data assistant. "
        "Choose EXACTLY ONE tool that can answer the question below.\n"
        "If the question is NOT about FVL transport data (trucks, empty km, costs, "
        "delays, deliveries, geography, loading factor) — e.g. weather, jokes, general "
        "knowledge, chit-chat — you MUST choose out_of_scope. When unsure, prefer "
        "out_of_scope over guessing a tool.\n\n"
        f"Tools:\n{tools}\n\nExamples:\n{examples}\n\nQuestion: {question}"
    )


def get_router_llm():
    llm = ChatOllama(model=MODEL, temperature=0, num_predict=200)
    return llm.with_structured_output(RouterDecision, method="json_schema")
