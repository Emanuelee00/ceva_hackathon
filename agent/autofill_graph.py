"""A genuine LangGraph cycle (not just a router): repeatedly picks the
best-fit candidate car and adds it to the lot until the loading gap closes
or no candidate fits — the dispatcher's "check -> propose -> add -> recheck"
loop, done by the agent in one click instead of by hand. Reuses
proposals.compute_proposals() as-is; no new selection logic invented here.
"""

from typing import Optional

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from loading_check import check_loading
from proposals import compute_proposals

MAX_ITERATIONS = 10


class AutoFillState(TypedDict):
    lot_car_ids: list
    lot_loading: float
    truck_max: float
    threshold: float
    added: list
    done: bool
    stop_reason: Optional[str]
    iterations: int


def build_autofill_graph(all_cars: list, trip: dict):
    def check(state):
        result = check_loading(state["lot_loading"], state["truck_max"], state["threshold"])
        if not result["alert"]:
            return {"done": True, "stop_reason": "optimized"}
        if state["iterations"] >= MAX_ITERATIONS:
            return {"done": True, "stop_reason": "max_iterations"}
        candidates = [c for c in all_cars if c["id"] not in state["lot_car_ids"]]
        proposals = compute_proposals(candidates, trip, state["lot_loading"], state["truck_max"], limit=1)
        if not proposals:
            return {"done": True, "stop_reason": "no_candidates"}
        return {"done": False}

    def pick_best(state):
        candidates = [c for c in all_cars if c["id"] not in state["lot_car_ids"]]
        best = compute_proposals(candidates, trip, state["lot_loading"], state["truck_max"], limit=1)[0]
        car = best["car"]
        entry = {"model": car["model"], "loadingRatio": car["loadingRatio"], "newTotal": best["newTotal"]}
        return {
            "lot_car_ids": state["lot_car_ids"] + [car["id"]],
            "lot_loading": best["newTotal"],
            "added": state["added"] + [entry],
            "iterations": state["iterations"] + 1,
        }

    def route_after_check(state):
        return END if state["done"] else "pick_best"

    g = StateGraph(AutoFillState)
    g.add_node("check", check)
    g.add_node("pick_best", pick_best)
    g.add_edge(START, "check")
    g.add_conditional_edges("check", route_after_check, {"pick_best": "pick_best", END: END})
    g.add_edge("pick_best", "check")

    return g.compile()
