# 📖 Chania Book Festival — Social Media Analytics

Streamlit dashboard για την ανάλυση της επικοινωνιακής στρατηγικής social media
του 5ου Φεστιβάλ Βιβλίου Χανίων, βασισμένο σε εξαγωγές Meta Business Suite
(Instagram Stories, Facebook Posts, Instagram Feed) για την περίοδο
Φεβρουάριος–Ιούλιος 2026.

## Τι δείχνει

- KPIs: δημοσιεύσεις, συνολική απήχηση, engagement, engagement rate
- Εξέλιξη απήχησης στον χρόνο, με highlight τη διάρκεια του φεστιβάλ (22–28/6)
- Σύγκριση pre-event / during / post-event περιόδου
- Απόδοση ανά κανάλι (Facebook vs Instagram) και ανά τύπο περιεχομένου (Reel, Carousel, Photo, Video...)
- Heatmap ημέρας/ώρας για βέλτιστο timing δημοσιεύσεων
- Top 10 δημοσιεύσεις με τη μεγαλύτερη απήχηση
- Λεπτομερής πίνακας σύγκρισης καναλιών (views, reach, engagement rate, likes/shares/comments)
- Earned media: ποιοι λογαριασμοί μας ανέφεραν/tag-άρισαν
- **Word cloud & συχνές λέξεις** από τα captions (χωρίς branding boilerplate)
- **Συγγραφείς/Ομιλητές**: heuristic εξαγωγή ονομάτων από τα κείμενα + απήχηση ανά όνομα
- **Κατηγοριοποίηση περιεχομένου** βάσει λέξεων-κλειδιών (συζήτηση, παρουσίαση βιβλίου, εργαστήριο, συνέντευξη, ξενάγηση, βράβευση/τελετή, ανακοίνωση/πρόγραμμα)
- **Instagram Stories metrics**: κλικ σε σύνδεσμο, επισκέψεις προφίλ, πατήματα sticker, νέοι followers, πλοήγηση
- **Αρνητικό feedback (Facebook)**: δημοσιεύσεις με "απόκρυψη"/"απόκρυψη όλων"
- Αυτόματα παραγόμενα strategic insights με βάση τα φιλτραρισμένα δεδομένα

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
│   └── data_loader.py      # Φόρτωση & ενοποίηση των 3 exports σε κοινό schema
└── data/
    ├── instagram_stories.csv
    ├── facebook_posts.csv
    └── instagram_feed.csv
```

## Ανανέωση δεδομένων

Κάθε φορά που κατεβάζεις νέο απολογιστικό από το Meta Business Suite
(Insights → Export data), αντικατέστησε το αντίστοιχο αρχείο στο φάκελο
`data/` διατηρώντας το ίδιο όνομα αρχείου. Το `data_loader.py` αναγνωρίζει
αυτόματα τις στήλες — αν το Meta αλλάξει τις ονομασίες στηλών σε νέο export,
πρέπει να ενημερωθούν τα `df["..."]` references στο αντίστοιχο `load_*()`.

Για να προσθέσεις δεδομένα από **επόμενο φεστιβάλ** (π.χ. 6ο Φεστιβάλ), το πιο
καθαρό είναι να προσθέσεις μια στήλη `edition` στο ενοποιημένο DataFrame ώστε
να μπορείς να συγκρίνεις έτος με έτος.

## Deploy στο Streamlit Community Cloud (δωρεάν)

1. Ανέβασε αυτό τον φάκελο σε ένα **public** (ή private με Streamlit for Teams)
   GitHub repo.
2. Πήγαινε στο [share.streamlit.io](https://share.streamlit.io), συνδέσου με
   GitHub, "New app" → επίλεξε το repo, branch `main`, main file `app.py`.
3. Πάτα Deploy. Κάθε `git push` στο repo θα κάνει auto-redeploy το app.

⚠️ Πριν κάνεις το repo public, σκέψου αν τα raw CSV (με τα ονόματα χρηστών
που μας ανέφεραν) πρέπει να μείνουν **private repo** αντί για public —
ειδικά αν περιέχουν προσωπικά δεδομένα τρίτων (GDPR).

## Σημείωση για την εξαγωγή ονομάτων

Η ενότητα "Συγγραφείς & Ομιλητές" χρησιμοποιεί ένα απλό regex πάνω σε
διαδοχικές κεφαλαιογράμματες λέξεις — όχι πραγματικό NER μοντέλο. Θα
συμπεριλάβει κατά καιρούς και θεσμικά ονόματα (π.χ. υπηρεσίες, τμήματα)
που δεν αποκλείστηκαν από τη λίστα `INSTITUTIONAL_ENTITIES` στο
`utils/text_analysis.py`. Αν θέλεις μεγαλύτερη ακρίβεια, το επόμενο βήμα
είναι να συνδέσεις ένα πραγματικό NER (π.χ. spaCy `el_core_news_sm`) —
κρατήσαμε το heuristic προσέγγιση εδώ για να μείνει το app ελαφρύ και χωρίς
βαριά dependencies.

## Ιδέες για επέκταση

- **Σύγκριση ετών**: όταν μαζευτούν δεδομένα από 2+ φεστιβάλ, πρόσθεσε
  φίλτρο edition-over-edition comparison.
- **NLP στα captions**: εντοπισμός λέξεων-κλειδιών / hashtags που συσχετίζονται
  με υψηλότερη απήχηση (μπορείς να αξιοποιήσεις τεχνικές αντίστοιχες με αυτές
  του MuseumsGR project για topic clustering).
- **Attribution links**: αν τα link clicks συνδέονται με Google Analytics του
  site του φεστιβάλ, μπορεί να προστεθεί funnel: reach → clicks → εισιτήρια.
- **Export σε PDF report**: αυτόματη παραγωγή απολογιστικού PDF για το ΔΣ /
  χορηγούς με βάση τα ίδια δεδομένα.
