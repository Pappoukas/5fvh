"""
Data loader & cleaner για τα απολογιστικά εξαγωγής του Meta Business Suite
(Instagram Stories, Facebook Posts, Instagram Feed) του Φεστιβάλ Βιβλίου Χανίων.

Ενοποιεί τα 3 heterogeneous exports σε ένα κοινό, καθαρό schema έτοιμο
για ανάλυση & οπτικοποίηση.
"""

import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Το επίσημο account/page του Φεστιβάλ - ό,τι άλλο account εμφανίζεται
# στα exports είναι "earned media" (αναφορές / συνεργασίες, όχι δικές μας δημοσιεύσεις)
OWNED_ACCOUNT_NAMES = {
    "Chania Book Festival",
    "Φεστιβάλ Βιβλίου Χανίων - Chania Book Festival",
}

FESTIVAL_START = pd.Timestamp("2026-06-22")
FESTIVAL_END = pd.Timestamp("2026-06-28 23:59:59")


def _phase(dt: pd.Timestamp) -> str:
    if pd.isna(dt):
        return "Άγνωστο"
    if dt < FESTIVAL_START:
        return "Πριν το Φεστιβάλ"
    if dt <= FESTIVAL_END:
        return "Κατά το Φεστιβάλ"
    return "Μετά το Φεστιβάλ"


def load_instagram_stories() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "instagram_stories.csv")
    df["dt"] = pd.to_datetime(df["Χρόνος δημοσίευσης"], errors="coerce")
    out = pd.DataFrame({
        "id": df["Αναγνωριστικό δημοσίευσης"],
        "account": df["Όνομα λογαριασμού"],
        "channel": "Instagram",
        "format": "Story",
        "text": df["Περιγραφή"].fillna(""),
        "dt": df["dt"],
        "views": df["Προβολές"].fillna(0),
        "reach": df["Απήχηση"].fillna(0),
        "likes": df["Μου αρέσει!"].fillna(0),
        "shares": df["Κοινοποιήσεις"].fillna(0),
        "comments": 0,
        "link": df["Μόνιμος σύνδεσμος"],
        "is_owned": True,
        "story_replies": df["Απαντήσεις"].fillna(0),
        "story_navigation": df["Πλοήγηση"].fillna(0),
        "story_sticker_taps": df["Πατήματα σε αυτοκόλλητο"].fillna(0),
        "story_profile_visits": df["Επισκέψεις στο προφίλ"].fillna(0),
        "story_link_clicks": df["Κλικ σε σύνδεσμο"].fillna(0),
        "story_new_follows": df["Πόσοι ακολουθούν"].fillna(0),
    })
    return out


def load_facebook_posts() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "facebook_posts.csv")
    df["dt"] = pd.to_datetime(df["Χρόνος δημοσίευσης"], errors="coerce")
    text = df["Τίτλος"].fillna("") + " " + df["Περιγραφή"].fillna("")
    out = pd.DataFrame({
        "id": df["Αναγνωριστικό δημοσίευσης"],
        "account": df["Όνομα σελίδας"],
        "channel": "Facebook",
        "format": df["Τύπος δημοσίευσης"].replace({
            "Φωτογραφίες": "Photo", "Photos": "Photo",
            "Βίντεο": "Video", "Videos": "Video",
            "Σύνδεσμοι": "Link", "Κείμενο": "Text",
            "Εκδηλώσεις": "Event", "Live": "Live",
        }),
        "text": text.str.strip(),
        "dt": df["dt"],
        "views": df["Προβολές"].fillna(0),
        "reach": df["Απήχηση"].fillna(0),
        "likes": df["Αντιδράσεις"].fillna(0),
        "shares": df["Κοινοποιήσεις"].fillna(0),
        "comments": df["Σχόλια"].fillna(0),
        "link": df["Μόνιμος σύνδεσμος"],
        "is_owned": df["Όνομα σελίδας"].isin(OWNED_ACCOUNT_NAMES),
        "fb_hide_all": df["Αρνητικά σχόλια από χρήστες: Απόκρυψη όλων"].fillna(0),
        "fb_hide": df["Αρνητικά σχόλια από χρήστες: Απόκρυψη"].fillna(0),
    })
    return out


def load_instagram_feed() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "instagram_feed.csv")
    df["dt"] = pd.to_datetime(df["Χρόνος δημοσίευσης"], errors="coerce")
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
        "dt": df["dt"],
        "views": df["Προβολές"].fillna(0),
        "reach": df["Απήχηση"].fillna(0),
        "likes": df["Μου αρέσει!"].fillna(0),
        "shares": df["Κοινοποιήσεις"].fillna(0),
        "comments": df["Σχόλια"].fillna(0),
        "link": df["Μόνιμος σύνδεσμος"],
        "is_owned": df["Όνομα λογαριασμού"].isin(OWNED_ACCOUNT_NAMES),
    })
    return out


def load_all() -> pd.DataFrame:
    """Επιστρέφει ένα ενοποιημένο DataFrame με όλες τις δημοσιεύσεις
    (δικές μας + earned media) και από τα 3 κανάλια."""
    frames = [load_instagram_stories(), load_facebook_posts(), load_instagram_feed()]
    df = pd.concat(frames, ignore_index=True)
    df = df.dropna(subset=["dt"])
    for col in ["views", "reach", "likes", "shares", "comments"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["engagement"] = df["likes"] + df["shares"] + df["comments"]
    df["engagement_rate"] = np.where(df["reach"] > 0, df["engagement"] / df["reach"], np.nan)
    df["phase"] = df["dt"].apply(_phase)
    df["weekday"] = df["dt"].dt.day_name()
    df["hour"] = df["dt"].dt.hour
    df["week"] = df["dt"].dt.isocalendar().week
    df["date"] = df["dt"].dt.date
    return df.sort_values("dt").reset_index(drop=True)
