# utils/data_loader.py (προσθήκες στο τέλος του αρχείου)

# Λίστα γνωστών ομιλητών/συγγραφέων (μπορεί να εμπλουτιστεί από το πρόγραμμα)
SPEAKERS = [
    "Orhan Pamuk", "Maurice Attia", "Jonathan Coe", "Leonardo Padura",
    "Hari Kunzru", "Niall Williams", "Katie Kitamura", "Alan Hollinghurst",
    "Caryl Ferey", "Vincenzo Latronico", "Eric Chacour", "Eric Mukendi",
    "Didier Aubourg", "Martin Glaz Serup", "Laura Cwiertnia", "Rodrigo Rey Rosa",
    "Alejandro Palomas", "Abi Daré", "Julianne Pachico", "Richard Gwyn",
    "Ghayath Almadhoun", "Eusebi Ayensa", "Dominic Amerena", "Meryem El Mehdati",
    "Στέφανος Τραχανάς", "Τίτος Πατρίκιος", "Παναγιώτης Σημανδηράκης",
    "Μανώλης Πιμπλής", "Κυριακή Μπεϊόγλου", "Παυλίνα Μάρβιν",
    "Φωτεινή Τσαλίκογλου", "Έρση Σωτηροπούλου", "Γιάννης Μακριδάκης",
    "Έλενα Μαρούτσου", "Μαρία Α. Ιωάννου", "Κυριάκος Χαρίτος",
    "Νίκος Δαββέτας", "Τάσος Σακελλαρόπουλος", "Μικέλα Χαρτουλάρη",
    "Αλεξάνδρα Χαΐνη", "Γιάννης Πανταζόπουλος", "Σταύρος Θεοδωράκης",
    "Παύλος Τσίμας", "Ξένια Κουναλάκη", "Πάνος Χαρίτος", "Πέτρος Κατσάκος",
    "Λένα Διβάνη", "Αργυρώ Μαντόγλου", "Ελένη Γιαννακάκη", "Σωτήρης Ρούσσος",
    "Χλόη Μπάλλα", "Κωνσταντίνος Πουλής", "Ιωσήφ Αλυγιζάκης",
    "Χρήστος Χωμενίδης", "Γιώργος Συμπάρδης", "Θράσος Καμινάκης",
    "Απόστολος Δοξιάδης", "Βασίλης Γκουρογιάννης", "Πολύνα Μπανά",
    "Ευάρεστος Πιμπλής", "Μαρία Λούκα", "Γιάννης Παλαβός",
    "Νάντια Αργυροπούλου", "Φραγκίσκη Αμπατζοπούλου"
]

# Λέξεις-κλειδιά για κατηγοριοποίηση περιεχομένου
CONTENT_CATEGORIES = {
    "Συζήτηση": ["συζήτηση", "διάλογος", "συνομιλία", "πάνελ", "συζητούν", "συνομιλούν"],
    "Παρουσίαση βιβλίου": ["παρουσίαση", "βιβλίο", "έκδοση", "κυκλοφορεί", "νέο βιβλίο", "τίτλο"],
    "Συνέντευξη": ["συνέντευξη", "μιλάει", "ακούστε", "συνέντευξη"],
    "Εργαστήριο": ["εργαστήριο", "masterclass", "βιωματικό", "workshop"],
    "Μουσική/Παράσταση": ["μουσική", "τραγούδι", "παράσταση", "αφήγηση", "συναυλία"],
    "Έκθεση": ["έκθεση", "εικαστική", "εγκαίνια", "ζωγράφος", "φωτογραφία"],
    "Ανακοίνωση": ["ανακοίνωση", "πρόγραμμα", "συνέντευξη τύπου", "απολογισμός"],
    "Στιγμιότυπο": ["στιγμιότυπο", "φωτογραφίες", "video highlights", "reel"]
}


def _extract_speakers(text: str) -> list:
    """Επιστρέφει τα ονόματα ομιλητών που βρίσκονται στο κείμενο."""
    found = []
    for name in SPEAKERS:
        if name.lower() in text.lower():
            found.append(name)
    return found


def _categorize_content(text: str) -> str:
    """Επιστρέφει την κατηγορία περιεχομένου με βάση λέξεις-κλειδιά."""
    text_lower = text.lower()
    for cat, keywords in CONTENT_CATEGORIES.items():
        if any(kw in text_lower for kw in keywords):
            return cat
    return "Άλλο"


# Τροποποιημένες συναρτήσεις load_* για να περιλαμβάνουν επιπλέον στήλες

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
        "comments": 0,  # no direct comments on stories
        "link": df["Μόνιμος σύνδεσμος"],
        "is_owned": True,
        # Extra story metrics
        "link_clicks": df["Κλικ σε σύνδεσμο"].fillna(0),
        "profile_visits": df["Επισκέψεις στο προφίλ"].fillna(0),
        "replies": df["Απαντήσεις"].fillna(0),
        "sticker_taps": df["Πατήματα σε αυτοκόλλητο"].fillna(0),
        "hides": 0,
        "hides_all": 0,
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
        # Facebook negative feedback
        "hides": df["Αρνητικά σχόλια από χρήστες: Απόκρυψη"].fillna(0),
        "hides_all": df["Αρνητικά σχόλια από χρήστες: Απόκρυψη όλων"].fillna(0),
        # Extra (fill with 0 for stories compatibility)
        "link_clicks": 0,
        "profile_visits": 0,
        "replies": 0,
        "sticker_taps": 0,
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
        "link_clicks": 0,
        "profile_visits": 0,
        "replies": 0,
        "sticker_taps": 0,
        "hides": 0,
        "hides_all": 0,
    })
    return out


def load_all() -> pd.DataFrame:
    """Επιστρέφει ενοποιημένο DataFrame με επιπλέον υπολογισμένες στήλες."""
    frames = [load_instagram_stories(), load_facebook_posts(), load_instagram_feed()]
    df = pd.concat(frames, ignore_index=True)
    df = df.dropna(subset=["dt"])
    for col in ["views", "reach", "likes", "shares", "comments", "link_clicks", "profile_visits", "replies", "sticker_taps", "hides", "hides_all"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["engagement"] = df["likes"] + df["shares"] + df["comments"]
    df["engagement_rate"] = np.where(df["reach"] > 0, df["engagement"] / df["reach"], np.nan)
    df["phase"] = df["dt"].apply(_phase)
    df["weekday"] = df["dt"].dt.day_name()
    df["hour"] = df["dt"].dt.hour
    df["week"] = df["dt"].dt.isocalendar().week
    df["date"] = df["dt"].dt.date

    # Εξαγωγή ομιλητών και κατηγορία περιεχομένου (μόνο για owned posts)
    df["speakers"] = df.apply(lambda row: _extract_speakers(row["text"]) if row["is_owned"] else [], axis=1)
    df["content_category"] = df.apply(lambda row: _categorize_content(row["text"]) if row["is_owned"] else "Άλλο", axis=1)

    return df.sort_values("dt").reset_index(drop=True)
