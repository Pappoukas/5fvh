"""
Εργαλεία ανάλυσης κειμένου για τα captions/περιγραφές των δημοσιεύσεων:
- καθαρισμός κειμένου & αφαίρεση επαναλαμβανόμενου boilerplate
- word frequency / word cloud
- heuristic εξαγωγή ονομάτων συγγραφέων/ομιλητών (regex-based, όχι πλήρες NER)
- κατηγοριοποίηση περιεχομένου βάσει λέξεων-κλειδιών
"""

import re
from collections import Counter

import pandas as pd

# --------------------------------------------------------------------- #
# Καθαρισμός κειμένου
# --------------------------------------------------------------------- #

# Το boilerplate block που επαναλαμβάνεται σχεδόν σε κάθε δημοσίευση
# (γενική περιγραφή του φεστιβάλ) — το αφαιρούμε πριν το word cloud / τις
# κατηγορίες, ώστε να μην κυριαρχεί σε κάθε ανάλυση.
_BOILERPLATE_PATTERNS = [
    r"5ο Φεστιβάλ Βιβλίου Χανίων.*?#\w*[Cc]hania[Bb]ook[Ff]estival",
    r"Το Φεστιβάλ Βιβλίου Χανίων πραγματοποιείται.*?πολιτιστικό χάρτη\.?",
    r"22[–\-]28 Ιουνίου 2026",
    r"«Κόσμοι σε σύγκρουση»",
]

GREEK_STOPWORDS = {
    "και", "να", "το", "τον", "την", "τα", "της", "του", "των", "τη", "τις",
    "στο", "στον", "στην", "στη", "στις", "στα", "με", "από", "για", "ή",
    "που", "είναι", "είχε", "έχει", "θα", "δεν", "μη", "μην", "ένα", "ένας",
    "μια", "μία", "ως", "αλλά", "όπως", "όπου", "όταν", "πως", "πού", "πώς",
    "εαν", "αν", "ότι", "ό,τι", "αυτό", "αυτή", "αυτός", "αυτά", "αυτούς",
    "εμείς", "εσείς", "τους", "τους", "μας", "σας", "τους", "ένας", "κάθε",
    "πολύ", "πιο", "πάνω", "κάτω", "μετά", "πριν", "ήδη", "ήταν", "είμαστε",
    "είστε", "είναι", "ό", "τι", "εδώ", "εκεί", "όλα", "όλες", "όλοι", "όλο",
    "καί", "στου", "στης", "επί", "υπό", "διά", "προς", "μέσα", "έξω", "ένα",
    "δύο", "τρία", "θέλει", "μπορεί", "μπορούν", "γίνεται", "γίνει",
    "είχαν", "έχουν", "έχει", "κατά", "μία", "λόγω", "μέχρι", "χωρίς",
}

# Λέξεις-branding/θεσμικές που επαναλαμβάνονται σε σχεδόν κάθε δημοσίευση
# και δεν αντιπροσωπεύουν θεματικό περιεχόμενο (venue, ημερομηνίες, συνδιοργανωτές γενικά).
DOMAIN_STOPWORDS = {
    "χανίων", "χανιά", "φεστιβάλ", "βιβλίου", "βιβλίο", "ιουνίου", "μαΐου",
    "ιουλίου", "φεβρουαρίου", "μαρτίου", "απριλίου", "συνδιοργάνωση",
    "συνδιοργανώνεται", "εκδόσεις", "θέατρο", "μίκης", "θεοδωράκης",
    "αρσενάλι", "μεγάλο", "ενετικό", "λιμάνι", "δήμος", "δήμου", "περιφέρεια",
    "κρήτης", "αίθουσα",
}
GREEK_STOPWORDS = GREEK_STOPWORDS | DOMAIN_STOPWORDS

# Λέξεις/φράσεις που ξέρουμε ότι είναι θεσμικά ονόματα, όχι πρόσωπα —
# χρησιμοποιούνται για να ΜΗΝ μπερδεύονται με ονόματα ομιλητών.
INSTITUTIONAL_ENTITIES = {
    "Δήμος Χανίων", "Περιφέρεια Κρήτης", "Chania Culture",
    "Φεστιβάλ Βιβλίου", "Μεγάλο Αρσενάλι", "Ενετικό Λιμάνι",
    "Θέατρο Μίκης", "Μίκης Θεοδωράκης", "Κόσμοι Σύγκρουση",
    "Municipality Of", "Region Of", "Εκδόσεις Πατάκη", "Εκδόσεις Άγρα",
    "Εκδόσεις Gutenberg", "Εκδόσεις Ίκαρος", "Ελληνική Λέσχη",
}


def strip_boilerplate(text: str) -> str:
    t = text or ""
    for pat in _BOILERPLATE_PATTERNS:
        t = re.sub(pat, " ", t, flags=re.IGNORECASE | re.DOTALL)
    return t


def clean_text(text: str) -> str:
    t = strip_boilerplate(text)
    t = re.sub(r"http\S+", " ", t)                      # links
    t = re.sub(r"[@#]\w+", " ", t)                       # mentions/hashtags
    t = re.sub(r"[^\wΑ-Ωα-ωΆ-Ώά-ώΪΫϊϋΐΰ\s]", " ", t)      # punctuation/emoji
    t = re.sub(r"\s+", " ", t).strip()
    return t


def word_frequencies(texts: pd.Series, min_len: int = 3, top_n: int = 100) -> dict:
    counter = Counter()
    for text in texts.fillna(""):
        cleaned = clean_text(text).lower()
        for word in cleaned.split():
            if len(word) < min_len:
                continue
            if word in GREEK_STOPWORDS:
                continue
            if word.isdigit():
                continue
            counter[word] += 1
    return dict(counter.most_common(top_n))


# --------------------------------------------------------------------- #
# Heuristic εξαγωγή ονομάτων (regex, όχι πλήρες NER)
# --------------------------------------------------------------------- #

# 2-3 διαδοχικές λέξεις με κεφαλαίο αρχικό γράμμα (ελληνικό ή λατινικό)
_NAME_PATTERN = re.compile(
    r"\b([Α-ΩΆ-Ώ][α-ωά-ώ]{2,}(?:\s+[Α-ΩΆ-Ώ][α-ωά-ώ]{2,}){1,2}"
    r"|[A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,}){1,2})\b"
)


def extract_names(text: str) -> list[str]:
    t = strip_boilerplate(text or "")
    # αφαίρεσε hashtags/links πρώτα ώστε να μη μολύνουν τα ονόματα
    t = re.sub(r"http\S+", " ", t)
    t = re.sub(r"#\w+", " ", t)
    candidates = _NAME_PATTERN.findall(t)
    names = []
    for c in candidates:
        if any(inst.lower() in c.lower() for inst in INSTITUTIONAL_ENTITIES):
            continue
        names.append(c.strip())
    return names


def build_names_table(df: pd.DataFrame, text_col: str = "text",
                       reach_col: str = "reach") -> pd.DataFrame:
    """Επιστρέφει DataFrame: name, mentions, total_reach, avg_reach."""
    rows = []
    for _, row in df.iterrows():
        for name in set(extract_names(row[text_col])):
            rows.append((name, row[reach_col]))
    if not rows:
        return pd.DataFrame(columns=["name", "mentions", "total_reach", "avg_reach"])
    tmp = pd.DataFrame(rows, columns=["name", "reach"])
    out = tmp.groupby("name").agg(
        mentions=("reach", "count"), total_reach=("reach", "sum"), avg_reach=("reach", "mean")
    ).reset_index().sort_values("total_reach", ascending=False)
    return out


# --------------------------------------------------------------------- #
# Κατηγοριοποίηση περιεχομένου βάσει λέξεων-κλειδιών
# --------------------------------------------------------------------- #

CONTENT_CATEGORIES = [
    # (κατηγορία, λέξεις-κλειδιά με σειρά προτεραιότητας)
    ("Συνέντευξη", ["συνέντευξη", "μιλάει στον", "μιλάει στην", "μιλά στον", "μιλά στην"]),
    ("Εργαστήριο", ["εργαστήρι", "εργαστήριο", "workshop"]),
    ("Ξενάγηση", ["ξενάγηση", "περιήγηση"]),
    ("Βράβευση / Τελετή", ["βράβευση", "βραβείο", "τελετή εγκαινίων", "εγκαίνια"]),
    ("Συζήτηση / Συνομιλία", ["συζήτηση", "συνομίλησε", "συνομιλία", "διάλογος", "συνομιλεί"]),
    ("Παρουσίαση βιβλίου", ["παρουσίαση", "παρουσιάζει", "παρουσιάζεται", "νέο βιβλίο", "βιβλίο του", "βιβλίο της"]),
    ("Ανακοίνωση / Πρόγραμμα", ["πρόγραμμα", "ανακοίνωση", "σας περιμένουμε", "έρχεται", "αντίστροφη μέτρηση"]),
]


def categorize(text: str) -> str:
    t = clean_text(text).lower()
    for label, keywords in CONTENT_CATEGORIES:
        if any(kw in t for kw in keywords):
            return label
    return "Άλλο"


def add_category_column(df: pd.DataFrame, text_col: str = "text") -> pd.DataFrame:
    df = df.copy()
    df["category"] = df[text_col].fillna("").apply(categorize)
    return df


# --------------------------------------------------------------------- #
# Hashtags
# --------------------------------------------------------------------- #

_HASHTAG_PATTERN = re.compile(r"#(\w+)", re.UNICODE)

# Το σταθερό branded hashtag εμφανίζεται σχεδόν παντού — εξαιρείται από τη
# σύγκριση απόδοσης ώστε να αναδειχθούν τα υπόλοιπα, πιο "θεματικά" hashtags.
BRAND_HASHTAGS = {"chaniabookfestival", "φεστιβάλβιβλίουχανίων", "cbf"}


def extract_hashtags(text: str) -> list[str]:
    if not text:
        return []
    return [h.lower() for h in _HASHTAG_PATTERN.findall(text)]


def build_hashtag_table(df: pd.DataFrame, text_col: str = "text",
                         reach_col: str = "reach", exclude_brand: bool = True) -> pd.DataFrame:
    """Επιστρέφει DataFrame: hashtag, posts, total_reach, avg_reach."""
    rows = []
    for _, row in df.iterrows():
        tags = set(extract_hashtags(row[text_col]))
        if exclude_brand:
            tags -= BRAND_HASHTAGS
        for tag in tags:
            rows.append((tag, row[reach_col]))
    if not rows:
        return pd.DataFrame(columns=["hashtag", "posts", "total_reach", "avg_reach"])
    tmp = pd.DataFrame(rows, columns=["hashtag", "reach"])
    out = tmp.groupby("hashtag").agg(
        posts=("reach", "count"), total_reach=("reach", "sum"), avg_reach=("reach", "mean")
    ).reset_index().sort_values("total_reach", ascending=False)
    return out
