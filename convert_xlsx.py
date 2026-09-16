"""Convert every sheet of the raw Excel files into CSV.

FVL - Transport Operations 2026.xlsx is excluded: its Data sheet is already
converted at data/csv/fvl_transport_2026.csv (the main analysis dataset),
re-converting it here would just duplicate a 100MB+ file.

Usage:
    make convert
    uv run python convert_xlsx.py
"""

from pathlib import Path

import pandas as pd

XLSX_DIR = Path("data/xlsx")
CSV_DIR = Path("data/csv")
SKIP = {"FVL - Transport Operations 2026.xlsx"}


def slug(name: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in name.lower()).strip("_")


def convert_file(path: Path) -> None:
    sheets = pd.read_excel(path, sheet_name=None, engine="openpyxl")
    stem = slug(path.stem)
    for sheet_name, df in sheets.items():
        df = df.dropna(how="all").dropna(axis=1, how="all")
        out = CSV_DIR / f"{stem}__{slug(sheet_name)}.csv"
        df.to_csv(out, index=False)
        print(f"{path.name} [{sheet_name}] -> {out} ({df.shape[0]} rows, {df.shape[1]} cols)")


def main() -> None:
    for path in sorted(XLSX_DIR.glob("*.xlsx")):
        if path.name in SKIP:
            print(f"Skipping {path.name} (already converted separately)")
            continue
        convert_file(path)


if __name__ == "__main__":
    main()
