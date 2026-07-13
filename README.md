# 📖 Chania Book Festival — Social Media Analytics

Streamlit dashboard για την ανάλυση της επικοινωνιακής στρατηγικής social media
του Φεστιβάλ Βιβλίου Χανίων, βασισμένο σε εξαγωγές Meta Business Suite
(Instagram Stories, Facebook Posts, Instagram Feed) για **3 διοργανώσεις**:

| Έτος | Διοργάνωση | Ημερομηνίες |
|---|---|---|
| 2024 | 3ο ΦΒΧ | 26–30 Ιουνίου 2024 |
| 2025 | 4ο ΦΒΧ | 25–29 Ιουνίου 2025 |
| 2026 | 5ο ΦΒΧ | 22–28 Ιουνίου 2026 |

## Τι δείχνει

- KPIs: δημοσιεύσεις, συνολική απήχηση, engagement, engagement rate
- Εξέλιξη απήχησης στον χρόνο, με highlight τη διάρκεια κάθε φεστιβάλ
- **Σύγκριση διοργανώσεων (Year-over-Year)**: δημοσιεύσεις/reach/views/engagement ανά έτος
- Σύγκριση pre-event / during / post-event περιόδου
- Απόδοση ανά κανάλι (Facebook vs Instagram) και ανά τύπο περιεχομένου
- Λεπτομερής πίνακας σύγκρισης καναλιών
- Heatmap ημέρας/ώρας για βέλτιστο timing δημοσιεύσεων
- Top 10 δημοσιεύσεις με τη μεγαλύτερη απήχηση
- Earned media: ποιοι λογαριασμοί μας ανέφεραν/tag-άρισαν
- Word cloud & συχνές λέξεις από τα captions (χωρίς branding boilerplate)
- Συγγραφείς/Ομιλητές: heuristic εξαγωγή ονομάτων + απήχηση ανά όνομα
- Κατηγοριοποίηση περιεχομένου βάσει λέξεων-κλειδιών
- Instagram Stories metrics: κλικ σε σύνδεσμο, επισκέψεις προφίλ, sticker taps, νέοι followers
- Αρνητικό feedback (Facebook): δημοσιεύσεις με "απόκρυψη"/"απόκρυψη όλων"
- **Διάρκεια βίντεο/story vs απήχηση**
- **Μήκος κειμένου vs engagement rate**
- **Απόδοση hashtags** (εκτός του σταθερού branded hashtag)
- **Ταχύτητα συσσώρευσης απήχησης** (proxy μέσω ημερών από τη δημοσίευση)
- Πλήρες χρονολόγιο αναρτήσεων (πότε δημοσιεύτηκε το καθετί)
- Ενότητα "Αυτόματα strategic insights" — έτοιμη στον κώδικα αλλά προσωρινά κρυφή
  (`SHOW_STRATEGIC_INSIGHTS = False` στην κορυφή του `app.py`)

## ⚠️ Σημείωση ποιότητας δεδομένων (2024)

Το export της Meta για το 2024 δεν περιλαμβάνει στήλη "Προβολές" (views) στα
Facebook posts, ούτε τα πεδία αρνητικού feedback. Ακόμη πιο σημαντικό: η στήλη
"Απήχηση" στα Instagram Stories του 2024 δείχνει μη ρεαλιστικά χαμηλές τιμές
(μέσος όρος ~6 ανά story, έναντι εκατοντάδων στο 2025/2026) — πιθανότατα το
Meta άλλαξε το τι μετρά αυτή η στήλη ή είχε ελλιπές tracking τότε. Η στήλη
"Προβολές" (views) είναι πιο αξιόπιστη για το 2024. Σύγκρινε έτη με αυτή την
επιφύλαξη κατά νου — το dashboard εμφανίζει σχετική προειδοποίηση.

## Τοπική εκτέλεση

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Δομή project

```
chania-book-festival-analytics/
├── app.py                  # Το Streamlit app
├── requirements.txt
├── utils/
│   ├── data_loader.py       # Φόρτωση & ενοποίηση πολυετών exports σε κοινό schema
│   └── text_analysis.py     # Word frequencies, ονόματα, κατηγορίες, hashtags
└── data/
    ├── 2024/
    │   ├── facebook_posts.csv
    │   ├── instagram_feed.csv
    │   └── instagram_stories.csv
    ├── 2025/ (ίδια δομή)
    └── 2026/ (ίδια δομή)
```

## Ανανέωση δεδομένων

Κάθε φορά που κατεβάζεις νέο απολογιστικό από το Meta Business Suite
(Insights → Export data), αντικατέστησε το αντίστοιχο αρχείο στο
`data/<έτος>/` διατηρώντας το ίδιο όνομα αρχείου. Το `data_loader.py`
αναγνωρίζει αυτόματα τις στήλες και είναι ανεκτικό σε απόντες στήλες
(π.χ. αν μια χρονιά λείπει το "Προβολές", απλά συμπληρώνεται με 0).

Για να προσθέσεις δεδομένα από **επόμενο φεστιβάλ** (π.χ. 6ο Φεστιβάλ, 2027):
1. Δημιούργησε φάκελο `data/2027/` με τα 3 CSV.
2. Πρόσθεσε το 2027 στη λίστα `YEARS` και τα σωστά `FESTIVAL_DATES` /
   `EDITION_LABELS` στο `utils/data_loader.py`.

## Σημείωση για την εξαγωγή ονομάτων

Η ενότητα "Συγγραφείς & Ομιλητές" χρησιμοποιεί ένα απλό regex πάνω σε
διαδοχικές κεφαλαιογράμματες λέξεις — όχι πραγματικό NER μοντέλο. Θα
συμπεριλάβει κατά καιρούς και θεσμικά ονόματα (π.χ. υπηρεσίες, τμήματα)
που δεν αποκλείστηκαν από τη λίστα `INSTITUTIONAL_ENTITIES` στο
`utils/text_analysis.py`. Αν θέλεις μεγαλύτερη ακρίβεια, το επόμενο βήμα
είναι να συνδέσεις ένα πραγματικό NER (π.χ. spaCy `el_core_news_sm`) —
κρατήσαμε το heuristic προσέγγιση εδώ για να μείνει το app ελαφρύ και χωρίς
βαριά dependencies.

## Deploy στο Streamlit Community Cloud (δωρεάν)

1. Ανέβασε αυτό τον φάκελο σε ένα **public** (ή private με Streamlit for Teams)
   GitHub repo.
2. Πήγαινε στο [share.streamlit.io](https://share.streamlit.io), συνδέσου με
   GitHub, "New app" → επίλεξε το repo, branch `main`, main file `app.py`.
3. Πάτα Deploy. Κάθε `git push` στο repo θα κάνει auto-redeploy το app.

⚠️ Πριν κάνεις το repo public, σκέψου αν τα raw CSV (με τα ονόματα χρηστών
που μας ανέφεραν) πρέπει να μείνουν **private repo** αντί για public —
ειδικά αν περιέχουν προσωπικά δεδομένα τρίτων (GDPR).

## Ιδέες για επέκταση

- **NLP στα captions**: εντοπισμός θεματικών clusters με τεχνικές αντίστοιχες
  με αυτές του MuseumsGR project.
- **Attribution links**: αν τα link clicks συνδέονται με Google Analytics του
  site του φεστιβάλ, μπορεί να προστεθεί funnel: reach → clicks → εισιτήρια.
- **Export σε PDF report**: αυτόματη παραγωγή απολογιστικού PDF για το ΔΣ /
  χορηγούς με βάση τα ίδια δεδομένα.
- **Πραγματικό NER** για ονόματα συγγραφέων/ομιλητών (spaCy `el_core_news_sm`).
