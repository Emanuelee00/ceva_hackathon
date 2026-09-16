"""LangGraph orchestration: a chat question is routed (via constrained
decoding) to a fixed tool, or a form submission provides the tool directly
and skips routing. Either way, execute() only ever calls verified Python
functions — the LLM never computes a number, only picks a tool and narrates.
"""

from typing import Optional

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from agent.llm import get_router_llm, router_prompt
from agent.tools import narrate, run_tool

FALLBACK_TEXT = (
    "That's outside what this dataset can answer — try asking about empty-km cost, "
    "backhaul matching, geographic demand mismatch, fleet concentration, delivery "
    "delays, or a truck's loading-factor history."
)


class AgentState(TypedDict):
    question: str
    tool: Optional[str]
    top_n: int
    truck_plate: Optional[str]
    entered_lf: Optional[float]
    result: Optional[dict]
    answer: Optional[str]


def build_graph(df, frames):
    def route(state):
        decision = get_router_llm().invoke(router_prompt(state["question"]))
        return {"tool": decision.tool.value, "top_n": decision.top_n}

    def execute(state):
        result = run_tool(
            state["tool"], df, frames, state.get("top_n", 10),
            state.get("truck_plate"), state.get("entered_lf"),
        )
        return {"result": result}

    def synthesize(state):
        return {"answer": narrate(state["tool"], state["result"])}

    def fallback(state):
        return {"answer": FALLBACK_TEXT}

    def entry_decision(state):
        if state.get("tool"):
            return "fallback" if state["tool"] == "out_of_scope" else "execute"
        return "route"

    def route_decision(state):
        return "fallback" if state["tool"] == "out_of_scope" else "execute"

    g = StateGraph(AgentState)
    g.add_node("route", route)
    g.add_node("execute", execute)
    g.add_node("synthesize", synthesize)
    g.add_node("fallback", fallback)

    g.add_conditional_edges(START, entry_decision, {"route": "route", "execute": "execute", "fallback": "fallback"})
    g.add_conditional_edges("route", route_decision, {"execute": "execute", "fallback": "fallback"})
    g.add_edge("execute", "synthesize")
    g.add_edge("synthesize", END)
    g.add_edge("fallback", END)

    return g.compile()
