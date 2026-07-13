"""
Data loader & cleaner για τα απολογιστικά εξαγωγής του Meta Business Suite
(Instagram Stories, Facebook Posts, Instagram Feed) — πολυετή δεδομένα
για το 3ο (2024), 4ο (2025) και 5ο (2026) Φεστιβάλ Βιβλίου Χανίων.

Ενοποιεί τα heterogeneous exports κάθε έτους σε ένα κοινό, καθαρό schema
έτοιμο για ανάλυση & οπτικοποίηση. Το export schema του Meta αλλάζει λίγο
από χρόνο σε χρόνο (νέες/λιγότερες στήλες) — ο loader είναι ανεκτικός σε
απόντες στήλες και τις γεμίζει με 0 όπου χρειάζεται.
"""

import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

YEARS = [2024, 2025, 2026]

# Το επίσημο account/page του Φεστιβάλ - ό,τι άλλο account εμφανίζεται
# στα exports είναι "earned media" (αναφορές / συνεργασίες, όχι δικές μας δημοσιεύσεις)
OWNED_ACCOUNT_NAMES = {
    "Chania Book Festival",
    "Φεστιβάλ Βιβλίου Χανίων - Chania Book Festival",
}

# Πραγματικές ημερομηνίες διεξαγωγής κάθε διοργάνωσης (πηγή: chania.gr, lifo.gr)
FESTIVAL_DATES = {
    2024: (pd.Timestamp("2024-06-26"), pd.Timestamp("2024-06-30 23:59:59")),  # 3ο ΦΒΧ
    2025: (pd.Timestamp("2025-06-25"), pd.Timestamp("2025-06-29 23:59:59")),  # 4ο ΦΒΧ
    2026: (pd.Timestamp("2026-06-22"), pd.Timestamp("2026-06-28 23:59:59")),  # 5ο ΦΒΧ
}
EDITION_LABELS = {2024: "3ο ΦΒΧ (2024)", 2025: "4ο ΦΒΧ (2025)", 2026: "5ο ΦΒΧ (2026)"}

# Backward-compatible aliases (χρησιμοποιούνται από παλαιότερο κώδικα/σελίδες)
FESTIVAL_START = FESTIVAL_DATES[2026][0]
FESTIVAL_END = FESTIVAL_DATES[2026][1]


def _col(df: pd.DataFrame, name: str, default=0):
    """Ασφαλής επιλογή στήλης: αν λείπει από το συγκεκριμένο export
    (π.χ. το Meta δεν την υποστήριζε ακόμα τη συγκεκριμένη χρονιά), γύρνα 0."""
    if name in df.columns:
        return pd.to_numeric(df[name], errors="coerce").fillna(default)
    return pd.Series(default, index=df.index)


def _phase(row) -> str:
    dt, year = row["dt"], row["year"]
    if pd.isna(dt) or year not in FESTIVAL_DATES:
        return "Άγνωστο"
    start, end = FESTIVAL_DATES[year]
    if dt < start:
        return "Πριν το Φεστιβάλ"
    if dt <= end:
        return "Κατά το Φεστιβάλ"
    return "Μετά το Φεστιβάλ"


def load_instagram_stories(year: int) -> pd.DataFrame:
    path = DATA_DIR / str(year) / "instagram_stories.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    dt = pd.to_datetime(df["Χρόνος δημοσίευσης"], errors="coerce")
    out = pd.DataFrame({
        "id": df["Αναγνωριστικό δημοσίευσης"],
        "account": df["Όνομα λογαριασμού"],
        "channel": "Instagram",
        "format": "Story",
        "text": df["Περιγραφή"].fillna(""),
        "duration_sec": _col(df, "Διάρκεια (δευτ.)", np.nan),
        "dt": dt,
        "views": _col(df, "Προβολές"),
        "reach": _col(df, "Απήχηση"),
        "likes": _col(df, "Μου αρέσει!"),
        "shares": _col(df, "Κοινοποιήσεις"),
        "comments": 0,
        "link": df["Μόνιμος σύνδεσμος"],
        "is_owned": True,
        "story_replies": _col(df, "Απαντήσεις"),
        "story_navigation": _col(df, "Πλοήγηση"),
        "story_sticker_taps": _col(df, "Πατήματα σε αυτοκόλλητο"),
        "story_profile_visits": _col(df, "Επισκέψεις στο προφίλ"),
        "story_link_clicks": _col(df, "Κλικ σε σύνδεσμο"),
        "story_new_follows": _col(df, "Πόσοι ακολουθούν"),
    })
    out["year"] = year
    return out


def load_facebook_posts(year: int) -> pd.DataFrame:
    path = DATA_DIR / str(year) / "facebook_posts.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    dt = pd.to_datetime(df["Χρόνος δημοσίευσης"], errors="coerce")
    text = df["Τίτλος"].fillna("") + " " + df["Περιγραφή"].fillna("")
    out = pd.DataFrame({
        "id": df["Αναγνωριστικό δημοσίευσης"],
        "account": df["Όνομα σελίδας"],
        "channel": "Facebook",
        "format": df["Τύπος δημοσίευσης"].replace({
            "Φωτογραφίες": "Photo", "Photos": "Photo",
            "Βίντεο": "Video", "Videos": "Video",
            "Σύνδεσμοι": "Link", "Κείμενο": "Text",
            "Εκδηλώσεις": "Event", "Live": "Live", "Reel": "Reel",
        }),
        "text": text.str.strip(),
        "duration_sec": _col(df, "Διάρκεια (δευτ.)", np.nan),
        "dt": dt,
        "views": _col(df, "Προβολές"),
        "reach": _col(df, "Απήχηση"),
        "likes": _col(df, "Αντιδράσεις"),
        "shares": _col(df, "Κοινοποιήσεις"),
        "comments": _col(df, "Σχόλια"),
        "link": df["Μόνιμος σύνδεσμος"],
        "is_owned": df["Όνομα σελίδας"].isin(OWNED_ACCOUNT_NAMES),
        "fb_hide_all": _col(df, "Αρνητικά σχόλια από χρήστες: Απόκρυψη όλων"),
        "fb_hide": _col(df, "Αρνητικά σχόλια από χρήστες: Απόκρυψη"),
    })
    out["year"] = year
    return out


def load_instagram_feed(year: int) -> pd.DataFrame:
    path = DATA_DIR / str(year) / "instagram_feed.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    dt = pd.to_datetime(df["Χρόνος δημοσίευσης"], errors="coerce")
    out = pd.DataFrame({
        "id": df["Αναγνωριστικό δημοσίευσης"],
        "account": df["Όνομα λογαριασμού"],
        "channel": "Instagram",
        "format": df["Τύπος δημοσίευσης"].replace({
            "Εναλλασσόμενες εικόνες IG": "Carousel",
            "IG reel": "Reel",
            "Εικόνα IG": "Image",
        }),
        "text": df["Περιγραφή"].fillna(""),
        "duration_sec": _col(df, "Διάρκεια (δευτ.)", np.nan),
        "dt": dt,
        "views": _col(df, "Προβολές"),
        "reach": _col(df, "Απήχηση"),
        "likes": _col(df, "Μου αρέσει!"),
        "shares": _col(df, "Κοινοποιήσεις"),
        "comments": _col(df, "Σχόλια"),
        "saves": _col(df, "Αποθηκεύσεις"),
        "link": df["Μόνιμος σύνδεσμος"],
        "is_owned": df["Όνομα λογαριασμού"].isin(OWNED_ACCOUNT_NAMES),
    })
    out["year"] = year
    return out


def load_all(years=None) -> pd.DataFrame:
    """Επιστρέφει ένα ενοποιημένο DataFrame με όλες τις δημοσιεύσεις
    (δικές μας + earned media), από όλα τα κανάλια και όλες τις διοργανώσεις."""
    years = years or YEARS
    frames = []
    for y in years:
        frames += [load_instagram_stories(y), load_facebook_posts(y), load_instagram_feed(y)]
    frames = [f for f in frames if len(f)]
    df = pd.concat(frames, ignore_index=True, sort=False)
    df = df.dropna(subset=["dt"])
    for col in ["views", "reach", "likes", "shares", "comments", "duration_sec"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ["views", "reach", "likes", "shares", "comments"]:
        df[col] = df[col].fillna(0)
    df["engagement"] = df["likes"] + df["shares"] + df["comments"]
    df["engagement_rate"] = np.where(df["reach"] > 0, df["engagement"] / df["reach"], np.nan)
    df["phase"] = df.apply(_phase, axis=1)
    df["edition"] = df["year"].map(EDITION_LABELS).fillna(df["year"].astype(str))
    df["weekday"] = df["dt"].dt.day_name()
    df["hour"] = df["dt"].dt.hour
    df["week"] = df["dt"].dt.isocalendar().week
    df["date"] = df["dt"].dt.date
    df["text_length"] = df["text"].fillna("").str.len()
    return df.sort_values("dt").reset_index(drop=True)
