"""
Φόρτωση δεδομένων απόδοσης ιστοσελίδας από Google Search Console exports
(chaniabookfestival.gr). Κάθε export είναι ένα .xlsx με sheets: Chart, Queries,
Pages, Countries, Devices, Search appearance, Filters.

Ο φάκελος data/website/ μπορεί να περιέχει πολλά τέτοια exports (ένα ανά
περίοδο/έτος) — ο loader τα διαβάζει όλα και τα ενοποιεί, αναγνωρίζοντας
αυτόματα το έτος από τις ημερομηνίες του κάθε αρχείου.
"""

import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "website"


def _read_export(path: Path) -> dict:
    xls = pd.ExcelFile(path)
    sheets = {}
    if "Chart" in xls.sheet_names:
        chart = pd.read_excel(xls, "Chart")
        chart.columns = ["date", "clicks", "impressions", "ctr", "position"]
        chart["date"] = pd.to_datetime(chart["date"])
        chart["year"] = chart["date"].dt.year
        sheets["daily"] = chart
    if "Queries" in xls.sheet_names:
        q = pd.read_excel(xls, "Queries")
        q.columns = ["query", "clicks", "impressions", "ctr", "position"]
        sheets["queries"] = q
    if "Pages" in xls.sheet_names:
        p = pd.read_excel(xls, "Pages")
        p.columns = ["page", "clicks", "impressions", "ctr", "position"]
        sheets["pages"] = p
    if "Countries" in xls.sheet_names:
        c = pd.read_excel(xls, "Countries")
        c.columns = ["country", "clicks", "impressions", "ctr", "position"]
        sheets["countries"] = c
    if "Devices" in xls.sheet_names:
        d = pd.read_excel(xls, "Devices")
        d.columns = ["device", "clicks", "impressions", "ctr", "position"]
        sheets["devices"] = d
    return sheets


def load_website_data(years=None) -> dict:
    """Διαβάζει όλα τα .xlsx exports στο data/website/ και τα ενοποιεί.
    Επιστρέφει dict με keys: daily, queries, pages, countries, devices —
    κάθε ένα DataFrame (με στήλη 'year' όπου έχει νόημα)."""
    if not DATA_DIR.exists():
        return {}
    files = sorted(DATA_DIR.glob("*.xlsx"))
    if not files:
        return {}

    daily_frames, query_frames, page_frames, country_frames, device_frames = [], [], [], [], []
    for f in files:
        sheets = _read_export(f)
        if "daily" in sheets:
            daily_frames.append(sheets["daily"])
        # Τα queries/pages/countries/devices είναι ήδη αθροισμένα ανά export
        # περίοδο (όχι ανά ημέρα) — προσθέτουμε ετικέτα πηγής αρχείου.
        for key, frames in [("queries", query_frames), ("pages", page_frames),
                             ("countries", country_frames), ("devices", device_frames)]:
            if key in sheets:
                df = sheets[key].copy()
                df["source_file"] = f.stem
                frames.append(df)

    result = {}
    if daily_frames:
        daily = pd.concat(daily_frames, ignore_index=True).drop_duplicates(subset=["date"])
        result["daily"] = daily.sort_values("date").reset_index(drop=True)
    if years is not None and "daily" in result:
        result["daily"] = result["daily"][result["daily"]["year"].isin(years)]
    if query_frames:
        result["queries"] = pd.concat(query_frames, ignore_index=True)
    if page_frames:
        result["pages"] = pd.concat(page_frames, ignore_index=True)
    if country_frames:
        result["countries"] = pd.concat(country_frames, ignore_index=True)
    if device_frames:
        result["devices"] = pd.concat(device_frames, ignore_index=True)
    return result
