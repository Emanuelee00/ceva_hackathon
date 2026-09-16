"""Fixed tool registry: the router LLM only ever picks a name from this
list; it never sees or writes pandas code. Each branch calls an existing,
already-verified analysis function — no new computation happens here.
"""

from cost_estimate import ALLIN_COST_PER_KM_EUR, CO2_PER_KM_G, FUEL_COST_PER_KM_EUR
from stats import compute_summary, delay_by_vehicle_count
from fleet_analysis import fleet_concentration
from geo_mismatch import compute_mismatch
from loading_factor_alert import check_alert
from matching_opportunity import match_opportunity

TOOL_DESCRIPTIONS = {
    "empty_km_cost": "Total empty-running km, % of distance driven, EUR/CO2 cost, top origin cities by empty km. Km a vuoto, costo.",
    "matching_opportunity": "Share of empty-running trips that already had a compatible nearby departure (backhaul-matching simulation). Abbinamento viaggi.",
    "geo_mismatch": "FVL delivery volume vs national car-registration volume by French department — over/under-served regions. Domanda territoriale.",
    "fleet_concentration": "Concentration of trips across real trucks (top-10% share), same-city trip share. Concentrazione flotta.",
    "delay_analysis": "Delivery delay in days broken down by number of vehicles per truck. Ritardi consegna.",
    "loading_factor_alert": "Check one truck's entered Loading Factor against its historical maximum and suggest an alternative if under-loaded. Alert riempimento camion.",
}


def run_tool(name: str, df, frames: dict, top_n: int = 10, truck_plate: str | None = None, entered_lf: float | None = None) -> dict:
    top_n = max(1, min(int(top_n), 50))
    if name == "empty_km_cost":
        s = compute_summary(df, frames["cost"])
        s["top_origins"] = s["top_origins"][:top_n]
        return s
    if name == "matching_opportunity":
        return match_opportunity(frames["match"])
    if name == "geo_mismatch":
        return compute_mismatch(df)
    if name == "fleet_concentration":
        return fleet_concentration(frames["fleet_raw"])
    if name == "delay_analysis":
        return {"rows": delay_by_vehicle_count(df)[:top_n]}
    if name == "loading_factor_alert":
        if not truck_plate or entered_lf is None:
            return {"info": "Use the dispatcher form below to check a specific truck."}
        return check_alert(df, truck_plate, entered_lf)
    raise ValueError(f"unknown tool: {name}")


def narrate(name: str, result: dict) -> str:
    """Deterministic Python templating, not an LLM call: a 3B local model
    reliably picks the right tool (see agent/llm.py) but was unreliable at
    freely narrating numbers (hallucinated units/values in testing) — so the
    final answer text is generated in code, guaranteeing every number shown
    is exactly what the analysis function returned.
    """
    if name == "empty_km_cost":
        return (f"{result['empty_share']:.1%} of all km driven is empty ({result['empty_km']:,.0f} km/year), "
                f"costing an estimated €{result['cost_allin']:,.0f}/year and {result['co2_t']:,.0f} t CO2.")
    if name == "matching_opportunity":
        return (f"{result['matched_share']:.1%} of empty-running trips already had a compatible departure "
                f"nearby — {result['matched_km_share']:.1%} of all empty km ({result['matched_km']:,.0f} km) "
                f"is addressable with better dispatch.")
    if name == "geo_mismatch":
        over, under = result["over_served"][0], result["under_served"][0]
        return (f"Correlation between deliveries and registrations across {result['n_depts']} departments is "
                f"{result['correlation']:.2f}. Most over-served: {over[0]} ({over[5]:.2f}x its registration "
                f"share). Most under-served: {under[0]} ({under[5]:.2f}x).")
    if name == "fleet_concentration":
        return (f"The top 10% of real trucks ({result['n_real_trucks']:,} total) carry "
                f"{result['top10_share']:.1%} of all trips. {result['same_city_share']:.1%} are same-city.")
    if name == "delay_analysis":
        rows = "; ".join(f"{int(n)} veh -> {mean:.1f}d avg" for n, _, mean, _ in result["rows"][:5])
        return f"Delay in days by vehicles-per-truck: {rows}."
    if name == "loading_factor_alert":
        if "info" in result:
            return result["info"]
        if result["alert"]:
            s = result.get("suggestion")
            tip = f" Consider truck {s['plate']} instead (historical max {s['historical_max']})." if s else ""
            return (f"ALERT: truck {result['plate']} is loaded at {result['entered_lf']}, {result['gap']} below "
                    f"its historical max of {result['historical_max']}.{tip}")
        return (f"OK: truck {result['plate']} loaded at {result['entered_lf']}, within {result['gap']} of its "
                f"historical max of {result['historical_max']}.")
    return str(result)


def methodology(name: str, result: dict) -> str | None:
    """Data + assumptions behind the answer, shown under an expander —
    judging criterion 03 requires disclosing assumptions, not just avoiding
    invented numbers. None where the answer is already fully self-explaining.
    """
    if name == "empty_km_cost":
        return (
            f"Real data: {result['n_trips']:,} real 2026 trips (deduplicated by Trip Leg Number), "
            f"{result['total_km']:,.0f} km total, of which {result['empty_km']:,.0f} km empty.\n\n"
            "Declared assumptions (not in the CEVA data — see cost_estimate.py):\n"
            f"- Fuel-only cost: {FUEL_COST_PER_KM_EUR} EUR/km (~35 L/100km diesel at ~1.60 EUR/L)\n"
            f"- All-in cost: {ALLIN_COST_PER_KM_EUR} EUR/km (fuel + driver + maintenance + tolls, typical EU "
            "heavy-truck road-freight range)\n"
            f"- CO2: {CO2_PER_KM_G} g/km (diesel HDV average EU emission factor)\n\n"
            f"All-in cost = {result['empty_km']:,.0f} empty km x {ALLIN_COST_PER_KM_EUR} EUR/km = "
            f"€{result['cost_allin']:,.0f}."
        )
    if name == "matching_opportunity":
        return (
            "Real data: every empty-running 2026 trip checked against real departure requests from the same "
            f"French department within {result['window_days']} days of the delivery that freed the truck — a "
            "measured lower bound (no truck-capacity assignment), not a promise."
        )
    return None
