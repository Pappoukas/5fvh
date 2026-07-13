"""
Chania Book Festival — Social Media Analytics Dashboard
Streamlit app για ανάλυση της επικοινωνιακής στρατηγικής social media
του Φεστιβάλ Βιβλίου Χανίων (Instagram Stories, Facebook, Instagram Feed).

Μετρική αναφοράς: ΠΡΟΒΟΛΕΣ (views), όχι απήχηση (reach). Η απήχηση δεν είναι
αθροιστική — ο ίδιος χρήστης μπορεί να μετρηθεί σε πολλαπλές δημοσιεύσεις,
οπότε το άθροισμα "Απήχηση" πολλών posts υπερεκτιμά σοβαρά το πραγματικό
μοναδικό κοινό. Οι προβολές (views) είναι πραγματικά αθροιστικές. Η μεμονωμένη
τιμή "Απήχηση" ενός post παραμένει έγκυρη ως στοιχείο ανά ανάρτηση και
εμφανίζεται σε μερικούς πίνακες λεπτομέρειας, αλλά δεν χρησιμοποιείται πλέον
πουθενά ως αθροισμένη/μέση μετρική.
"""

import os

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib
import matplotlib.pyplot as plt
from wordcloud import WordCloud

from utils.data_loader import load_all, FESTIVAL_DATES, EDITION_LABELS
from utils.text_analysis import (
    word_frequencies, build_names_table, add_category_column, build_hashtag_table,
)

GREEK_FONT_PATH = os.path.join(matplotlib.get_data_path(), "fonts", "ttf", "DejaVuSans.ttf")

# Toggle: η ενότητα "Αυτόματα strategic insights" είναι έτοιμη στον κώδικα
# αλλά κρατιέται κρυφή προς το παρόν. Άλλαξέ το σε True όποτε θέλεις να
# ξαναεμφανιστεί.
SHOW_STRATEGIC_INSIGHTS = False

st.set_page_config(
    page_title="Chania Book Festival — Social Analytics",
    page_icon="📖",
    layout="wide",
)

# ---------------------------------------------------------------- DATA ----
@st.cache_data
def get_data():
    return load_all()

df = get_data()

# ------------------------------------------------------------- SIDEBAR ----
st.sidebar.title("📖 Φίλτρα")

editions = st.sidebar.multiselect(
    "Διοργάνωση",
    sorted(df["edition"].unique(), key=lambda e: str(e)),
    default=sorted(df["edition"].unique(), key=lambda e: str(e)),
)
channels = st.sidebar.multiselect(
    "Κανάλι", sorted(df["channel"].unique()), default=sorted(df["channel"].unique())
)
own_filter = st.sidebar.radio(
    "Πηγή δημοσίευσης",
    ["Όλες", "Μόνο δικές μας", "Μόνο earned media / αναφορές"],
    index=0,
)
date_min, date_max = df["date"].min(), df["date"].max()
date_range = st.sidebar.date_input(
    "Εύρος ημερομηνιών", value=(date_min, date_max), min_value=date_min, max_value=date_max
)

fdf = df[df["channel"].isin(channels) & df["edition"].isin(editions)]
if own_filter == "Μόνο δικές μας":
    fdf = fdf[fdf["is_owned"]]
elif own_filter == "Μόνο earned media / αναφορές":
    fdf = fdf[~fdf["is_owned"]]
if isinstance(date_range, tuple) and len(date_range) == 2:
    fdf = fdf[(fdf["date"] >= date_range[0]) & (fdf["date"] <= date_range[1])]

st.sidebar.markdown("---")
st.sidebar.caption(
    "Δεδομένα: εξαγωγές Meta Business Suite, "
    f"{date_min.strftime('%d/%m/%Y')} – {date_max.strftime('%d/%m/%Y')}, "
    "3 διοργανώσεις (2024–2026).\n\n"
    "⚠️ Το 2024 έχει σοβαρά ελλιπή δεδομένα στην πηγή: 0 προβολές για Facebook "
    "(η στήλη δεν υπήρχε στο export τότε) και σχεδόν καθόλου προβολές για τα "
    "Instagram Stories. Σύγκρινε το 2024 με μεγάλη επιφύλαξη.\n\n"
    "📏 Μετρική αναφοράς: **προβολές (views)**, όχι απήχηση — η απήχηση δεν "
    "αθροίζεται σωστά μεταξύ πολλών δημοσιεύσεων."
)

# --------------------------------------------------------------- TITLE ----
st.title("📖 Φεστιβάλ Βιβλίου Χανίων — Social Media Analytics")
st.caption(
    "Insights για τη στρατηγική επικοινωνίας & τις μελλοντικές αποφάσεις της ομάδας — "
    "3ο (2024), 4ο (2025) & 5ο (2026) Φεστιβάλ"
)

# ----------------------------------------------------------------- KPIs ---
owned = fdf[fdf["is_owned"]]
earned = fdf[~fdf["is_owned"]]

if len(owned) == 0:
    st.warning("Δεν υπάρχουν δεδομένα για τα επιλεγμένα φίλτρα. Δοκίμασε να επιλέξεις τουλάχιστον μία διοργάνωση/κανάλι.")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Δημοσιεύσεις (δικές μας)", f"{len(owned):,}")
c2.metric("Συνολικές προβολές (views)", f"{int(owned['views'].sum()):,}")
c3.metric("Αλληλεπιδράσεις", f"{int(owned['engagement'].sum()):,}")
avg_er = owned.loc[owned["reach"] > 0, "engagement_rate"].mean()
c4.metric("Μέσο engagement rate", f"{avg_er:.1%}" if pd.notna(avg_er) else "—")
st.caption(
    "Το engagement rate υπολογίζεται ως αλληλεπιδράσεις/απήχηση ανά μεμονωμένη δημοσίευση και μετά "
    "παίρνεται ο μέσος όρος — αυτό είναι έγκυρο (δεν αθροίζει reach), σε αντίθεση με ένα «σύνολο απήχησης»."
)

st.markdown("---")

# ---------------------------------------------------------- TIMELINE -----
st.subheader("📈 Εξέλιξη προβολών στον χρόνο")
weekly = (
    owned.groupby(pd.Grouper(key="dt", freq="W"))["views"]
    .sum()
    .reset_index()
)
fig = px.area(weekly, x="dt", y="views", labels={"dt": "Εβδομάδα", "views": "Προβολές"})
for yr in sorted(owned["year"].dropna().unique()):
    if yr in FESTIVAL_DATES:
        start, end = FESTIVAL_DATES[yr]
        fig.add_vrect(
            x0=start, x1=end,
            fillcolor="orange", opacity=0.15, line_width=0,
            annotation_text=EDITION_LABELS.get(yr, str(yr)), annotation_position="top left",
        )
st.plotly_chart(fig, width='stretch')

phase_summary = (
    owned.groupby("phase")["views"].agg(["count", "sum", "mean"]).reindex(
        ["Πριν το Φεστιβάλ", "Κατά το Φεστιβάλ", "Μετά το Φεστιβάλ"]
    )
)
pc1, pc2, pc3 = st.columns(3)
for col, phase in zip([pc1, pc2, pc3], phase_summary.index):
    row = phase_summary.loc[phase]
    if pd.isna(row["count"]) or row["count"] == 0:
        col.metric(phase, "—", "0 posts στο επιλεγμένο εύρος")
    else:
        col.metric(phase, f"{int(row['sum']):,} views", f"{int(row['count'])} posts · μ.ό. {int(row['mean']):,}")

st.markdown("---")

# --------------------------------------------------- YEAR-OVER-YEAR -----
st.subheader("📅 Σύγκριση διοργανώσεων (Year-over-Year)")
st.caption(
    "⚠️ Το 2024 δεν έχει καθόλου δεδομένα προβολών για Facebook (η στήλη έλειπε από το "
    "export της χρονιάς) και σχεδόν καθόλου για τα Instagram Stories — η στήλη «2024» "
    "στα παρακάτω γραφήματα θα εμφανίζεται τεχνητά χαμηλή."
)
yoy = owned.groupby("edition").agg(
    posts=("id", "count"),
    total_views=("views", "sum"),
    total_engagement=("engagement", "sum"),
    avg_engagement_rate=("engagement_rate", "mean"),
).reset_index()
yoy["edition_sort"] = yoy["edition"].str.extract(r"\((\d+)\)").astype(int)
yoy = yoy.sort_values("edition_sort")

ycol1, ycol2 = st.columns(2)
with ycol1:
    fig_yoy_posts = px.bar(yoy, x="edition", y="posts", labels={"edition": "", "posts": "Δημοσιεύσεις"})
    st.plotly_chart(fig_yoy_posts, width='stretch')
with ycol2:
    fig_yoy_views = px.bar(yoy, x="edition", y="total_views", labels={"edition": "", "total_views": "Σύνολο προβολών"})
    st.plotly_chart(fig_yoy_views, width='stretch')

yoy_display = yoy.drop(columns=["edition_sort"]).copy()
yoy_display["avg_engagement_rate"] = (yoy_display["avg_engagement_rate"] * 100).round(2).astype(str) + "%"
for c in ["total_views", "total_engagement"]:
    yoy_display[c] = yoy_display[c].astype(int)
yoy_display.columns = ["Διοργάνωση", "Δημοσιεύσεις", "Σύνολο προβολών", "Αλληλεπιδράσεις", "Μέσο engagement rate"]
st.dataframe(yoy_display, width='stretch', hide_index=True)

st.markdown("---")

# ------------------------------------------------------ CHANNEL/FORMAT ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📊 Απόδοση ανά κανάλι")
    st.caption("Facebook, Instagram Feed και Instagram Stories εμφανίζονται ως 3 ξεχωριστά κανάλια.")
    ch = owned.groupby("channel").agg(
        posts=("id", "count"), views=("views", "sum"), engagement=("engagement", "sum")
    ).reset_index()
    fig_ch = px.bar(ch, x="channel", y="views", text="posts",
                     labels={"views": "Συνολικές προβολές", "channel": "Κανάλι"})
    fig_ch.update_traces(texttemplate="%{text} posts", textposition="outside")
    st.plotly_chart(fig_ch, width='stretch')

with col_right:
    st.subheader("🎞️ Απόδοση ανά τύπο περιεχομένου")
    fmt = owned.groupby("format").agg(
        posts=("id", "count"), avg_views=("views", "mean")
    ).reset_index().sort_values("avg_views", ascending=False)
    fig_fmt = px.bar(fmt, x="format", y="avg_views", text="posts",
                      labels={"avg_views": "Μέσες προβολές/post", "format": "Τύπος"})
    fig_fmt.update_traces(texttemplate="n=%{text}", textposition="outside")
    st.plotly_chart(fig_fmt, width='stretch')

st.markdown("#### 🔍 Λεπτομερής σύγκριση καναλιών")
detail = owned.groupby("channel").agg(
    posts=("id", "count"),
    total_views=("views", "sum"),
    avg_views=("views", "mean"),
    median_views=("views", "median"),
    total_engagement=("engagement", "sum"),
    avg_engagement_rate=("engagement_rate", "mean"),
    likes=("likes", "sum"),
    shares=("shares", "sum"),
    comments=("comments", "sum"),
).reset_index()
detail_display = detail.copy()
detail_display["avg_views"] = detail_display["avg_views"].round(0).astype(int)
detail_display["median_views"] = detail_display["median_views"].round(0).astype(int)
detail_display["avg_engagement_rate"] = (detail_display["avg_engagement_rate"] * 100).round(2).astype(str) + "%"
for c in ["total_views", "total_engagement", "likes", "shares", "comments"]:
    detail_display[c] = detail_display[c].astype(int)
detail_display.columns = [
    "Κανάλι", "Δημοσιεύσεις", "Σύνολο views", "Μέσο views",
    "Median views", "Αλληλεπιδράσεις", "Μέσο engagement rate",
    "Likes", "Shares", "Comments",
]
st.dataframe(detail_display, width='stretch', hide_index=True)

st.markdown("---")

# ------------------------------------------------------- BEST TIMING -----
st.subheader("🕒 Πότε αποδίδουν καλύτερα οι δημοσιεύσεις")
heat = owned.groupby(["weekday", "hour"])["views"].mean().reset_index()
weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
gr_days = {"Monday": "Δευ", "Tuesday": "Τρι", "Wednesday": "Τετ", "Thursday": "Πεμ",
           "Friday": "Παρ", "Saturday": "Σαβ", "Sunday": "Κυρ"}
heat["weekday"] = pd.Categorical(heat["weekday"], categories=weekday_order, ordered=True)
heat["weekday_gr"] = heat["weekday"].map(gr_days)
heat_pivot = heat.pivot(index="weekday_gr", columns="hour", values="views").reindex(
    [gr_days[d] for d in weekday_order]
)
fig_heat = px.imshow(
    heat_pivot, aspect="auto", color_continuous_scale="Oranges",
    labels=dict(x="Ώρα", y="Ημέρα", color="Μέσες προβολές"),
)
st.plotly_chart(fig_heat, width='stretch')

st.markdown("---")

# ----------------------------------------------------------- TOP POSTS ---
st.subheader("🏆 Top 10 δημοσιεύσεις (δικές μας) ανά προβολές")
top = owned.nlargest(10, "views")[["dt", "channel", "format", "text", "views", "reach", "engagement", "link"]].copy()
top["text"] = top["text"].str.slice(0, 90) + "…"
top["dt"] = top["dt"].dt.strftime("%d/%m/%Y %H:%M")
top.columns = ["Ημερομηνία/Ώρα", "Κανάλι", "Τύπος", "Κείμενο", "Views", "Reach", "Engagement", "Σύνδεσμος"]
st.dataframe(top, width='stretch', hide_index=True)
st.caption("Η στήλη «Reach» δείχνει την απήχηση αυτής της συγκεκριμένης ανάρτησης (έγκυρη ανά post, δεν αθροίζεται).")

st.markdown("---")

# -------------------------------------------------------- EARNED MEDIA ---
st.subheader("🤝 Earned media — ποιοι μας ανέφεραν")
if len(earned):
    em = earned.groupby("account").agg(mentions=("id", "count")).reset_index().sort_values(
        "mentions", ascending=False
    )
    fig_em = px.bar(em, x="account", y="mentions", labels={"account": "Λογαριασμός", "mentions": "Αναφορές"})
    st.plotly_chart(fig_em, width='stretch')
    st.caption(
        "Το Meta δεν παρέχει δεδομένα απήχησης/views/engagement για δημοσιεύσεις τρίτων λογαριασμών — "
        "μετράμε μόνο τον αριθμό αναφορών/tags."
    )
else:
    st.info("Δεν υπάρχουν καταγεγραμμένες αναφορές τρίτων στο επιλεγμένο εύρος.")

st.markdown("---")

# --------------------------------------------------------- WORD CLOUD ---
st.subheader("☁️ Word Cloud & συχνές λέξεις")
st.caption(
    "Το επαναλαμβανόμενο boilerplate κείμενο (γενική περιγραφή φεστιβάλ, hashtags, "
    "σύνδεσμοι) έχει αφαιρεθεί ώστε να αναδειχθούν οι πραγματικές θεματικές."
)
freqs = word_frequencies(owned["text"], top_n=120)
if freqs:
    wcol1, wcol2 = st.columns([2, 1])
    with wcol1:
        wc = WordCloud(
            width=1000, height=500, background_color="white",
            font_path=GREEK_FONT_PATH, colormap="Oranges",
        ).generate_from_frequencies(freqs)
        fig_wc, ax_wc = plt.subplots(figsize=(10, 5))
        ax_wc.imshow(wc, interpolation="bilinear")
        ax_wc.axis("off")
        st.pyplot(fig_wc)
        plt.close(fig_wc)
    with wcol2:
        top_words = pd.DataFrame(list(freqs.items())[:15], columns=["Λέξη", "Συχνότητα"])
        st.dataframe(top_words, width='stretch', hide_index=True)
else:
    st.info("Δεν υπάρχει αρκετό κείμενο στο επιλεγμένο εύρος.")

st.markdown("---")

# ---------------------------------------------------- AUTHORS/SPEAKERS ---
st.subheader("🗣️ Συγγραφείς & Ομιλητές — ποιοι φέρνουν τις περισσότερες προβολές")
st.caption(
    "Heuristic εξαγωγή ονομάτων (regex σε διαδοχικές λέξεις με κεφαλαίο αρχικό) — "
    "όχι πλήρες NER, οπότε ενδέχεται να περιλαμβάνει και μη-πρόσωπα. Χρήσιμο ως πρώτη ένδειξη."
)
names_df = build_names_table(owned, reach_col="views")
if len(names_df):
    top_names = names_df.head(20).copy()
    top_names["avg_reach"] = top_names["avg_reach"].round(0).astype(int)
    top_names["total_reach"] = top_names["total_reach"].astype(int)
    top_names.columns = ["Όνομα", "Αναφορές", "Συνολικές προβολές", "Μέσες προβολές"]
    st.dataframe(top_names, width='stretch', hide_index=True)
else:
    st.info("Δεν εντοπίστηκαν ονόματα στο επιλεγμένο εύρος.")

st.markdown("---")

# ------------------------------------------------------ CATEGORIES ------
st.subheader("🏷️ Κατηγοριοποίηση περιεχομένου")
st.caption(
    "Αυτόματη κατηγοριοποίηση βάσει λέξεων-κλειδιών στο κείμενο "
    "(συζήτηση, παρουσίαση βιβλίου, εργαστήριο, συνέντευξη, ξενάγηση, βράβευση/τελετή, ανακοίνωση/πρόγραμμα)."
)
cat_df = add_category_column(owned)
cat_summary = cat_df.groupby("category").agg(
    posts=("id", "count"), avg_views=("views", "mean"), total_views=("views", "sum")
).reset_index().sort_values("total_views", ascending=False)
ccol1, ccol2 = st.columns([1, 1])
with ccol1:
    fig_cat = px.bar(cat_summary, x="category", y="total_views", text="posts",
                      labels={"category": "Κατηγορία", "total_views": "Συνολικές προβολές"})
    fig_cat.update_traces(texttemplate="n=%{text}", textposition="outside")
    st.plotly_chart(fig_cat, width='stretch')
with ccol2:
    fig_cat_avg = px.bar(cat_summary.sort_values("avg_views", ascending=False),
                          x="category", y="avg_views",
                          labels={"category": "Κατηγορία", "avg_views": "Μέσες προβολές/post"})
    st.plotly_chart(fig_cat_avg, width='stretch')

st.markdown("---")

# ------------------------------------------------- INSTAGRAM STORIES ----
st.subheader("📱 Instagram Stories — ειδικές μετρικές")
stories = owned[owned["channel"] == "Instagram Stories"]
if len(stories):
    scol1, scol2, scol3, scol4, scol5 = st.columns(5)
    scol1.metric("Απαντήσεις (replies)", f"{int(stories['story_replies'].sum()):,}")
    scol2.metric("Κλικ σε σύνδεσμο", f"{int(stories['story_link_clicks'].sum()):,}")
    scol3.metric("Επισκέψεις προφίλ", f"{int(stories['story_profile_visits'].sum()):,}")
    scol4.metric("Πατήματα sticker", f"{int(stories['story_sticker_taps'].sum()):,}")
    scol5.metric("Νέοι followers", f"{int(stories['story_new_follows'].sum()):,}")

    st.caption(
        "Η «Πλοήγηση» (forward/back taps) δείχνει πόσο κρατάει την προσοχή ένα story: "
        f"μέσος όρος {stories['story_navigation'].mean():.0f} ανά story."
    )
    story_top = stories.nlargest(5, "story_link_clicks")[
        ["dt", "text", "views", "story_link_clicks", "story_profile_visits", "link"]
    ].copy()
    if story_top["story_link_clicks"].sum() > 0:
        story_top["dt"] = story_top["dt"].dt.strftime("%d/%m/%Y %H:%M")
        story_top["text"] = story_top["text"].str.slice(0, 60) + "…"
        st.markdown("**Stories με τα περισσότερα κλικ σε σύνδεσμο:**")
        st.dataframe(story_top, width='stretch', hide_index=True)
else:
    st.info("Δεν υπάρχουν Instagram Stories στο επιλεγμένο εύρος/φίλτρα.")

st.markdown("---")

# --------------------------------------------------- NEGATIVE FEEDBACK --
st.subheader("👎 Αρνητικά σχόλια χρηστών (Facebook)")
fb_owned = owned[owned["channel"] == "Facebook"]
if len(fb_owned) and ("fb_hide_all" in fb_owned.columns):
    hide_all_n = int(fb_owned["fb_hide_all"].fillna(0).sum())
    hide_n = int(fb_owned["fb_hide"].fillna(0).sum())
    ncol1, ncol2 = st.columns(2)
    ncol1.metric("«Απόκρυψη όλων» (hide all future posts)", hide_all_n)
    ncol2.metric("«Απόκρυψη» (hide this post)", hide_n)
    affected = fb_owned[(fb_owned["fb_hide_all"].fillna(0) > 0) | (fb_owned["fb_hide"].fillna(0) > 0)]
    if len(affected):
        aff_display = affected[["dt", "text", "views", "fb_hide_all", "fb_hide", "link"]].copy()
        aff_display["dt"] = aff_display["dt"].dt.strftime("%d/%m/%Y %H:%M")
        aff_display["text"] = aff_display["text"].str.slice(0, 70) + "…"
        st.markdown("**Δημοσιεύσεις με καταγεγραμμένο αρνητικό feedback:**")
        st.dataframe(aff_display, width='stretch', hide_index=True)
    st.caption(
        "Οι αριθμοί είναι πολύ μικροί σε απόλυτους όρους σε σχέση με το σύνολο των δημοσιεύσεων — "
        "δεν φαίνεται συστηματικό πρόβλημα, αλλά αξίζει να ελέγχονται οι συγκεκριμένες δημοσιεύσεις."
    )
else:
    st.info("Δεν υπάρχουν δεδομένα αρνητικού feedback στο επιλεγμένο εύρος/φίλτρα.")

st.markdown("---")

# ------------------------------------------------ DURATION VS VIEWS -----
st.subheader("🎬 Διάρκεια βίντεο/story vs προβολές")
dur = owned[owned["duration_sec"].notna() & (owned["duration_sec"] > 0)].copy()
if len(dur) >= 5:
    dur["duration_bucket"] = pd.cut(
        dur["duration_sec"],
        bins=[0, 5, 15, 30, 60, 120, 1e9],
        labels=["≤5s", "6-15s", "16-30s", "31-60s", "61-120s", ">120s"],
    )
    dcol1, dcol2 = st.columns(2)
    with dcol1:
        fig_dur_scatter = px.scatter(
            dur, x="duration_sec", y="views", color="format",
            labels={"duration_sec": "Διάρκεια (δευτ.)", "views": "Προβολές", "format": "Τύπος"},
            hover_data=["text"],
        )
        st.plotly_chart(fig_dur_scatter, width='stretch')
    with dcol2:
        dur_bucket_summary = dur.groupby("duration_bucket", observed=True).agg(
            posts=("id", "count"), avg_views=("views", "mean")
        ).reset_index()
        fig_dur_bucket = px.bar(dur_bucket_summary, x="duration_bucket", y="avg_views", text="posts",
                                 labels={"duration_bucket": "Διάρκεια", "avg_views": "Μέσες προβολές"})
        fig_dur_bucket.update_traces(texttemplate="n=%{text}", textposition="outside")
        st.plotly_chart(fig_dur_bucket, width='stretch')
    corr = dur["duration_sec"].corr(dur["views"])
    st.caption(f"Συσχέτιση διάρκειας–προβολών: r ≈ {corr:.2f} (κοντά στο 0 = ασθενής σχέση).")
else:
    st.info("Δεν υπάρχουν αρκετές δημοσιεύσεις με καταγεγραμμένη διάρκεια στο επιλεγμένο εύρος.")

st.markdown("---")

# --------------------------------------------- CAPTION LENGTH VS ENG. ---
st.subheader("✏️ Μήκος κειμένου vs engagement rate")
cl = owned[(owned["text_length"] > 0) & owned["engagement_rate"].notna()].copy()
if len(cl) >= 5:
    cl["length_bucket"] = pd.cut(
        cl["text_length"],
        bins=[0, 50, 150, 300, 600, 1e9],
        labels=["≤50 χαρ.", "51-150", "151-300", "301-600", ">600"],
    )
    lcol1, lcol2 = st.columns(2)
    with lcol1:
        fig_len_scatter = px.scatter(
            cl, x="text_length", y="engagement_rate", color="channel",
            labels={"text_length": "Μήκος κειμένου (χαρακτήρες)", "engagement_rate": "Engagement rate"},
        )
        fig_len_scatter.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig_len_scatter, width='stretch')
    with lcol2:
        len_bucket_summary = cl.groupby("length_bucket", observed=True).agg(
            posts=("id", "count"), avg_er=("engagement_rate", "mean")
        ).reset_index()
        fig_len_bucket = px.bar(len_bucket_summary, x="length_bucket", y="avg_er", text="posts",
                                 labels={"length_bucket": "Μήκος κειμένου", "avg_er": "Μέσο engagement rate"})
        fig_len_bucket.update_yaxes(tickformat=".1%")
        fig_len_bucket.update_traces(texttemplate="n=%{text}", textposition="outside")
        st.plotly_chart(fig_len_bucket, width='stretch')
    corr_len = cl["text_length"].corr(cl["engagement_rate"])
    st.caption(f"Συσχέτιση μήκους κειμένου–engagement rate: r ≈ {corr_len:.2f}.")
else:
    st.info("Δεν υπάρχουν αρκετά δεδομένα κειμένου/engagement στο επιλεγμένο εύρος.")

st.markdown("---")

# ------------------------------------------------- HASHTAG PERFORMANCE --
st.subheader("🏷️ Απόδοση hashtags")
st.caption(
    "Εξαιρείται το σταθερό branded hashtag (#chaniabookfestival) ώστε να αναδειχθούν "
    "τα πιο 'θεματικά' hashtags."
)
ht_df = build_hashtag_table(owned, reach_col="views")
if len(ht_df):
    htcol1, htcol2 = st.columns(2)
    with htcol1:
        top_ht_views = ht_df.nlargest(15, "total_reach")
        fig_ht = px.bar(top_ht_views, x="hashtag", y="total_reach", text="posts",
                         labels={"hashtag": "Hashtag", "total_reach": "Συνολικές προβολές"})
        fig_ht.update_traces(texttemplate="n=%{text}", textposition="outside")
        st.plotly_chart(fig_ht, width='stretch')
    with htcol2:
        ht_display = ht_df.head(20).copy()
        ht_display["avg_reach"] = ht_display["avg_reach"].round(0).astype(int)
        ht_display["total_reach"] = ht_display["total_reach"].astype(int)
        ht_display.columns = ["Hashtag", "Δημοσιεύσεις", "Συνολικές προβολές", "Μέσες προβολές"]
        st.dataframe(ht_display, width='stretch', hide_index=True)
else:
    st.info("Δεν εντοπίστηκαν hashtags (πέρα από το branded) στο επιλεγμένο εύρος.")

st.markdown("---")

# --------------------------------------------------- VIEWS VELOCITY -----
st.subheader("⏱️ Ταχύτητα συσσώρευσης προβολών")
st.caption(
    "Το export του Meta δεν δίνει ωριαία στοιχεία, οπότε αυτό είναι ένα proxy: "
    "συγκρίνει τις καταγεγραμμένες προβολές με το πόσες μέρες έχουν περάσει από τη δημοσίευση "
    "μέχρι την ημερομηνία εξαγωγής δεδομένων (12/7 κάθε έτους). Αν οι πρόσφατες δημοσιεύσεις "
    "έχουν συστηματικά χαμηλότερες προβολές, σημαίνει ότι οι προβολές συνεχίζουν να ανεβαίνουν με τον χρόνο."
)
velocity = owned.copy()
export_cutoffs = {y: pd.Timestamp(f"{y}-07-12 23:59:59") for y in velocity["year"].unique()}
velocity["days_since_post"] = velocity.apply(
    lambda r: (export_cutoffs[r["year"]] - r["dt"]).days, axis=1
)
velocity = velocity[velocity["days_since_post"] >= 0]
if len(velocity) >= 5:
    velocity["recency_bucket"] = pd.cut(
        velocity["days_since_post"],
        bins=[-1, 1, 3, 7, 14, 30, 1e9],
        labels=["0-1 μέρες", "2-3", "4-7", "8-14", "15-30", ">30"],
    )
    vel_summary = velocity.groupby("recency_bucket", observed=True).agg(
        posts=("id", "count"), avg_views=("views", "mean")
    ).reset_index()
    fig_vel = px.bar(vel_summary, x="recency_bucket", y="avg_views", text="posts",
                      labels={"recency_bucket": "Μέρες από τη δημοσίευση έως την εξαγωγή", "avg_views": "Μέσες προβολές"})
    fig_vel.update_traces(texttemplate="n=%{text}", textposition="outside")
    st.plotly_chart(fig_vel, width='stretch')
else:
    st.info("Δεν υπάρχουν αρκετά δεδομένα για αυτή την ανάλυση στο επιλεγμένο εύρος.")

st.markdown("---")

# ------------------------------------------------------ POSTING DATES ---
st.subheader("🗓️ Πότε έγιναν οι αναρτήσεις")
st.caption(
    "Πλήρες χρονολόγιο των αναρτήσεων: πόσες έγιναν ανά μήνα/εβδομάδα, "
    "ημερολογιακή πυκνότητα, και αναλυτική λίστα με ημερομηνία/ώρα κάθε δημοσίευσης."
)

pcol1, pcol2 = st.columns(2)
with pcol1:
    st.markdown("**Αναρτήσεις ανά μήνα**")
    monthly_counts = (
        owned.groupby(owned["dt"].dt.to_period("M"))["id"].count().reset_index()
    )
    monthly_counts["dt"] = monthly_counts["dt"].astype(str)
    monthly_counts.columns = ["Μήνας", "Αναρτήσεις"]
    fig_month = px.bar(monthly_counts, x="Μήνας", y="Αναρτήσεις")
    st.plotly_chart(fig_month, width='stretch')

with pcol2:
    st.markdown("**Αναρτήσεις ανά κανάλι/τύπο & εβδομάδα**")
    weekly_counts = (
        owned.groupby([pd.Grouper(key="dt", freq="W"), "channel"])["id"]
        .count()
        .reset_index()
        .rename(columns={"dt": "Εβδομάδα", "id": "Αναρτήσεις", "channel": "Κανάλι"})
    )
    fig_week_count = px.bar(
        weekly_counts, x="Εβδομάδα", y="Αναρτήσεις", color="Κανάλι", barmode="stack"
    )
    for yr in sorted(owned["year"].dropna().unique()):
        if yr in FESTIVAL_DATES:
            start, end = FESTIVAL_DATES[yr]
            fig_week_count.add_vrect(x0=start, x1=end, fillcolor="orange", opacity=0.12, line_width=0)
    st.plotly_chart(fig_week_count, width='stretch')

st.markdown("**Ημερολογιακή πυκνότητα αναρτήσεων** (ημέρα × ώρα, αριθμός δημοσιεύσεων)")
count_heat = owned.groupby(["weekday", "hour"])["id"].count().reset_index()
count_heat["weekday"] = pd.Categorical(count_heat["weekday"], categories=weekday_order, ordered=True)
count_heat["weekday_gr"] = count_heat["weekday"].map(gr_days)
count_heat_pivot = count_heat.pivot(index="weekday_gr", columns="hour", values="id").reindex(
    [gr_days[d] for d in weekday_order]
)
fig_count_heat = px.imshow(
    count_heat_pivot, aspect="auto", color_continuous_scale="Blues",
    labels=dict(x="Ώρα", y="Ημέρα", color="Αναρτήσεις"),
)
st.plotly_chart(fig_count_heat, width='stretch')

with st.expander("📋 Αναλυτική λίστα όλων των αναρτήσεων (ημερομηνία/ώρα, κανάλι, τύπος)"):
    schedule_table = owned[["dt", "channel", "format", "text", "views", "link"]].copy()
    schedule_table["dt"] = schedule_table["dt"].dt.strftime("%d/%m/%Y %H:%M")
    schedule_table["text"] = schedule_table["text"].str.slice(0, 60) + "…"
    schedule_table = schedule_table.sort_values("dt", ascending=False)
    schedule_table.columns = ["Ημερομηνία/Ώρα", "Κανάλι", "Τύπος", "Κείμενο", "Προβολές", "Σύνδεσμος"]
    st.dataframe(schedule_table, width='stretch', hide_index=True)

st.markdown("---")

# --------------------------------------------------------- STRATEGY -----
# Η ενότητα κρατιέται στον κώδικα αλλά είναι κρυφή προς το παρόν
# (SHOW_STRATEGIC_INSIGHTS = False στην κορυφή του αρχείου).
if SHOW_STRATEGIC_INSIGHTS:
    st.subheader("💡 Αυτόματα strategic insights")

    insights = []

    best_fmt = fmt.iloc[0]["format"] if len(fmt) else None
    if best_fmt:
        insights.append(
            f"Ο τύπος περιεχομένου **{best_fmt}** έχει τις περισσότερες μέσες προβολές/δημοσίευση — "
            "αξίζει μεγαλύτερη προτεραιότητα στο content plan."
        )

    best_day_row = heat.groupby("weekday_gr")["views"].mean().idxmax()
    insights.append(
        f"Η ημέρα με τις περισσότερες μέσες προβολές είναι **{best_day_row}** — "
        "καλό timing για τις πιο σημαντικές ανακοινώσεις."
    )

    pre_sum = phase_summary.loc["Πριν το Φεστιβάλ", "sum"]
    during_sum = phase_summary.loc["Κατά το Φεστιβάλ", "sum"]
    post_sum = phase_summary.loc["Μετά το Φεστιβάλ", "sum"]
    if pd.notna(pre_sum) and pd.notna(during_sum) and pre_sum and during_sum:
        ratio = during_sum / pre_sum
        insights.append(
            f"Οι προβολές κατά τη διάρκεια του φεστιβάλ ήταν **{ratio:.1f}×** περισσότερες σε σχέση με "
            "την περίοδο πριν — η ένταση δημοσιεύσεων τις ημέρες του event αποδίδει, αλλά "
            f"σημαίνει επίσης ότι η pre-event περίοδος (~{pre_sum:,.0f} views σε σύνολο) χρειάζεται "
            "πιο στοχευμένο, όχι απλώς πιο συχνό, περιεχόμενο."
        )
    if pd.notna(post_sum) and pd.notna(during_sum) and post_sum and during_sum:
        drop = 1 - (post_sum / during_sum)
        insights.append(
            f"Μετά τη λήξη του φεστιβάλ οι προβολές μειώθηκαν κατά **{drop:.0%}** — "
            "recap/highlight περιεχόμενο τις πρώτες 5-7 ημέρες μετά μπορεί να επιμηκύνει τη ζωή της καμπάνιας."
        )

    if len(earned):
        top_partner = em.iloc[0]["account"]
        insights.append(
            f"Ο λογαριασμός **{top_partner}** μας ανέφερε τις περισσότερες φορές — "
            "καλός υποψήφιος για πιο συστηματική συνεργασία / cross-posting στο επόμενο φεστιβάλ."
        )

    for i in insights:
        st.markdown(f"- {i}")

    st.caption(
        "Τα insights αυτά παράγονται αυτόματα από τα φιλτραρισμένα δεδομένα. "
        "Χρησιμοποιήστε τα φίλτρα στο πλάι για να εστιάσετε ανά κανάλι / περίοδο / πηγή."
    )
