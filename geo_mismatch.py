"""Cross FVL delivery volume by department against SDES new-car registration
volume by department, to check whether the transport network's geography
matches where demand actually is.

Caveat (disclosed on the dashboard, not hidden): SDES data is for 2025, the
FVL data is 2026 — used here as a demand-geography proxy, not an exact
year-to-year comparison.
"""

import pandas as pd

REG_PATH = "data/csv/donnees_immat_regions_departement_vp_v2__neuf_departement.csv"
MIN_DELIVERIES = 200


def department(zip_code) -> str:
    return str(zip_code).strip().zfill(5)[:2]


def compute_mismatch(df: pd.DataFrame) -> dict:
    deliveries = df.dropna(subset=["Delivery Zip Code"]).copy()
    deliveries["dept"] = deliveries["Delivery Zip Code"].apply(department)
    fvl = deliveries.groupby("dept").size().rename("fvl_deliveries").reset_index()

    reg = pd.read_csv(REG_PATH, dtype={"code_dep": str})
    reg = reg[reg["code_dep"] != "00"][["code_dep", "departement", "immat_2025"]]
    reg = reg.rename(columns={"code_dep": "dept"})

    m = fvl.merge(reg, on="dept", how="inner")
    m["fvl_share"] = m["fvl_deliveries"] / m["fvl_deliveries"].sum()
    m["reg_share"] = m["immat_2025"] / m["immat_2025"].sum()
    m["index"] = m["fvl_share"] / m["reg_share"]
    sized = m[m["fvl_deliveries"] >= MIN_DELIVERIES]

    def top(rows) -> list:
        return [(r.departement, r.dept, int(r.fvl_deliveries), r.fvl_share, r.reg_share, r.index) for r in rows.itertuples()]

    return {
        "n_depts": len(m),
        "correlation": m["fvl_deliveries"].corr(m["immat_2025"]),
        "over_served": top(sized.sort_values("index", ascending=False).head(5)),
        "under_served": top(sized.sort_values("index").head(5)),
    }
