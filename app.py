"""
Chania Book Festival — Social Media Analytics Dashboard
Streamlit app για ανάλυση της επικοινωνιακής στρατηγικής social media
του 5ου Φεστιβάλ Βιβλίου Χανίων (Instagram Stories, Facebook, Instagram Feed).
"""

import os

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib
import matplotlib.pyplot as plt
from wordcloud import WordCloud

from utils.data_loader import load_all, FESTIVAL_START, FESTIVAL_END
from utils.text_analysis import word_frequencies, build_names_table, add_category_column

GREEK_FONT_PATH = os.path.join(matplotlib.get_data_path(), "fonts", "ttf", "DejaVuSans.ttf")

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

fdf = df[df["channel"].isin(channels)]
if own_filter == "Μόνο δικές μας":
    fdf = fdf[fdf["is_owned"]]
elif own_filter == "Μόνο earned media / αναφορές":
    fdf = fdf[~fdf["is_owned"]]
if isinstance(date_range, tuple) and len(date_range) == 2:
    fdf = fdf[(fdf["date"] >= date_range[0]) & (fdf["date"] <= date_range[1])]

st.sidebar.markdown("---")
st.sidebar.caption(
    "Δεδομένα: εξαγωγές Meta Business Suite, "
    f"{date_min.strftime('%d/%m/%Y')} – {date_max.strftime('%d/%m/%Y')}.\n\n"
    "Φεστιβάλ: 22–28 Ιουνίου 2026."
)

# --------------------------------------------------------------- TITLE ----
st.title("📖 5ο Φεστιβάλ Βιβλίου Χανίων — Social Media Analytics")
st.caption("Insights για τη στρατηγική επικοινωνίας & τις μελλοντικές αποφάσεις της ομάδας")

# ----------------------------------------------------------------- KPIs ---
owned = fdf[fdf["is_owned"]]
earned = fdf[~fdf["is_owned"]]

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Δημοσιεύσεις (δικές μας)", f"{len(owned):,}")
c2.metric("Συνολική απήχηση (reach)", f"{int(owned['reach'].sum()):,}")
c3.metric("Σύνολο engagement", f"{int(owned['engagement'].sum()):,}")
avg_er = owned.loc[owned["reach"] > 0, "engagement_rate"].mean()
c4.metric("Μέσο engagement rate", f"{avg_er:.1%}" if pd.notna(avg_er) else "—")
c5.metric("Αναφορές από τρίτους (earned)", f"{len(earned):,}")

st.markdown("---")

# ---------------------------------------------------------- TIMELINE -----
st.subheader("📈 Εξέλιξη απήχησης στον χρόνο")
weekly = (
    owned.groupby(pd.Grouper(key="dt", freq="W"))["reach"]
    .sum()
    .reset_index()
)
fig = px.area(weekly, x="dt", y="reach", labels={"dt": "Εβδομάδα", "reach": "Απήχηση"})
fig.add_vrect(
    x0=FESTIVAL_START, x1=FESTIVAL_END,
    fillcolor="orange", opacity=0.15, line_width=0,
    annotation_text="Διάρκεια Φεστιβάλ", annotation_position="top left",
)
st.plotly_chart(fig, width='stretch')

phase_summary = (
    owned.groupby("phase")["reach"].agg(["count", "sum", "mean"]).reindex(
        ["Πριν το Φεστιβάλ", "Κατά το Φεστιβάλ", "Μετά το Φεστιβάλ"]
    )
)
pc1, pc2, pc3 = st.columns(3)
for col, phase in zip([pc1, pc2, pc3], phase_summary.index):
    row = phase_summary.loc[phase]
    col.metric(phase, f"{int(row['sum']):,} reach", f"{int(row['count'])} posts · μ.ό. {int(row['mean']):,}")

st.markdown("---")

# ------------------------------------------------------ CHANNEL/FORMAT ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📊 Απόδοση ανά κανάλι")
    ch = owned.groupby("channel").agg(
        posts=("id", "count"), reach=("reach", "sum"), engagement=("engagement", "sum")
    ).reset_index()
    fig_ch = px.bar(ch, x="channel", y="reach", text="posts",
                     labels={"reach": "Συνολική απήχηση", "channel": "Κανάλι"})
    fig_ch.update_traces(texttemplate="%{text} posts", textposition="outside")
    st.plotly_chart(fig_ch, width='stretch')

with col_right:
    st.subheader("🎞️ Απόδοση ανά τύπο περιεχομένου")
    fmt = owned.groupby("format").agg(
        posts=("id", "count"), avg_reach=("reach", "mean")
    ).reset_index().sort_values("avg_reach", ascending=False)
    fig_fmt = px.bar(fmt, x="format", y="avg_reach", text="posts",
                      labels={"avg_reach": "Μέση απήχηση/post", "format": "Τύπος"})
    fig_fmt.update_traces(texttemplate="n=%{text}", textposition="outside")
    st.plotly_chart(fig_fmt, width='stretch')

st.markdown("#### 🔍 Λεπτομερής σύγκριση καναλιών")
detail = owned.groupby("channel").agg(
    posts=("id", "count"),
    total_views=("views", "sum"),
    total_reach=("reach", "sum"),
    avg_reach=("reach", "mean"),
    median_reach=("reach", "median"),
    total_engagement=("engagement", "sum"),
    avg_engagement_rate=("engagement_rate", "mean"),
    likes=("likes", "sum"),
    shares=("shares", "sum"),
    comments=("comments", "sum"),
).reset_index()
detail_display = detail.copy()
detail_display["avg_reach"] = detail_display["avg_reach"].round(0).astype(int)
detail_display["median_reach"] = detail_display["median_reach"].round(0).astype(int)
detail_display["avg_engagement_rate"] = (detail_display["avg_engagement_rate"] * 100).round(2).astype(str) + "%"
for c in ["total_views", "total_reach", "total_engagement", "likes", "shares", "comments"]:
    detail_display[c] = detail_display[c].astype(int)
detail_display.columns = [
    "Κανάλι", "Δημοσιεύσεις", "Σύνολο views", "Σύνολο reach", "Μέσο reach",
    "Median reach", "Σύνολο engagement", "Μέσο engagement rate",
    "Likes", "Shares", "Comments",
]
st.dataframe(detail_display, width='stretch', hide_index=True)

st.markdown("---")

# ------------------------------------------------------- BEST TIMING -----
st.subheader("🕒 Πότε αποδίδουν καλύτερα οι δημοσιεύσεις")
heat = owned.groupby(["weekday", "hour"])["reach"].mean().reset_index()
weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
gr_days = {"Monday": "Δευ", "Tuesday": "Τρι", "Wednesday": "Τετ", "Thursday": "Πεμ",
           "Friday": "Παρ", "Saturday": "Σαβ", "Sunday": "Κυρ"}
heat["weekday"] = pd.Categorical(heat["weekday"], categories=weekday_order, ordered=True)
heat["weekday_gr"] = heat["weekday"].map(gr_days)
heat_pivot = heat.pivot(index="weekday_gr", columns="hour", values="reach").reindex(
    [gr_days[d] for d in weekday_order]
)
fig_heat = px.imshow(
    heat_pivot, aspect="auto", color_continuous_scale="Oranges",
    labels=dict(x="Ώρα", y="Ημέρα", color="Μέση απήχηση"),
)
st.plotly_chart(fig_heat, width='stretch')

st.markdown("---")

# ----------------------------------------------------------- TOP POSTS ---
st.subheader("🏆 Top 10 δημοσιεύσεις (δικές μας) ανά απήχηση")
top = owned.nlargest(10, "reach")[["dt", "channel", "format", "text", "reach", "engagement", "link"]].copy()
top["text"] = top["text"].str.slice(0, 90) + "…"
top["dt"] = top["dt"].dt.strftime("%d/%m/%Y %H:%M")
st.dataframe(top, width='stretch', hide_index=True)

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
        "Το Meta δεν παρέχει δεδομένα απήχησης/engagement για δημοσιεύσεις τρίτων λογαριασμών — "
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
    with wcol2:
        top_words = pd.DataFrame(list(freqs.items())[:15], columns=["Λέξη", "Συχνότητα"])
        st.dataframe(top_words, width='stretch', hide_index=True)
else:
    st.info("Δεν υπάρχει αρκετό κείμενο στο επιλεγμένο εύρος.")

st.markdown("---")

# ---------------------------------------------------- AUTHORS/SPEAKERS ---
st.subheader("🗣️ Συγγραφείς & Ομιλητές — ποιοι φέρνουν τη μεγαλύτερη απήχηση")
st.caption(
    "Heuristic εξαγωγή ονομάτων (regex σε διαδοχικές λέξεις με κεφαλαίο αρχικό) — "
    "όχι πλήρες NER, οπότε ενδέχεται να περιλαμβάνει και μη-πρόσωπα. Χρήσιμο ως πρώτη ένδειξη."
)
names_df = build_names_table(owned)
if len(names_df):
    top_names = names_df.head(20).copy()
    top_names["avg_reach"] = top_names["avg_reach"].round(0).astype(int)
    top_names["total_reach"] = top_names["total_reach"].astype(int)
    top_names.columns = ["Όνομα", "Αναφορές", "Συνολική απήχηση", "Μέση απήχηση"]
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
    posts=("id", "count"), avg_reach=("reach", "mean"), total_reach=("reach", "sum")
).reset_index().sort_values("total_reach", ascending=False)
ccol1, ccol2 = st.columns([1, 1])
with ccol1:
    fig_cat = px.bar(cat_summary, x="category", y="total_reach", text="posts",
                      labels={"category": "Κατηγορία", "total_reach": "Συνολική απήχηση"})
    fig_cat.update_traces(texttemplate="n=%{text}", textposition="outside")
    st.plotly_chart(fig_cat, width='stretch')
with ccol2:
    fig_cat_avg = px.bar(cat_summary.sort_values("avg_reach", ascending=False),
                          x="category", y="avg_reach",
                          labels={"category": "Κατηγορία", "avg_reach": "Μέση απήχηση/post"})
    st.plotly_chart(fig_cat_avg, width='stretch')

st.markdown("---")

# ------------------------------------------------- INSTAGRAM STORIES ----
st.subheader("📱 Instagram Stories — ειδικές μετρικές")
stories = owned[owned["format"] == "Story"]
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
        ["dt", "text", "reach", "story_link_clicks", "story_profile_visits", "link"]
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
        aff_display = affected[["dt", "text", "reach", "fb_hide_all", "fb_hide", "link"]].copy()
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

# --------------------------------------------------------- STRATEGY -----
st.subheader("💡 Αυτόματα strategic insights")

insights = []

best_fmt = fmt.iloc[0]["format"] if len(fmt) else None
if best_fmt:
    insights.append(
        f"Ο τύπος περιεχομένου **{best_fmt}** έχει τη μεγαλύτερη μέση απήχηση/δημοσίευση — "
        "αξίζει μεγαλύτερη προτεραιότητα στο content plan."
    )

best_day_row = heat.groupby("weekday_gr")["reach"].mean().idxmax()
insights.append(
    f"Η ημέρα με τη μεγαλύτερη μέση απήχηση είναι **{best_day_row}** — "
    "καλό timing για τις πιο σημαντικές ανακοινώσεις."
)

pre_sum = phase_summary.loc["Πριν το Φεστιβάλ", "sum"]
during_sum = phase_summary.loc["Κατά το Φεστιβάλ", "sum"]
post_sum = phase_summary.loc["Μετά το Φεστιβάλ", "sum"]
if pre_sum and during_sum:
    ratio = during_sum / pre_sum
    insights.append(
        f"Η απήχηση κατά τη διάρκεια του φεστιβάλ ήταν **{ratio:.1f}×** μεγαλύτερη σε σχέση με "
        "την περίοδο πριν — η ένταση δημοσιεύσεων τις ημέρες του event αποδίδει, αλλά "
        f"σημαίνει επίσης ότι η pre-event περίοδος (~{pre_sum:,.0f} reach σε σύνολο) χρειάζεται "
        "πιο στοχευμένο, όχι απλώς πιο συχνό, περιεχόμενο."
    )
if post_sum and during_sum:
    drop = 1 - (post_sum / during_sum)
    insights.append(
        f"Μετά τη λήξη του φεστιβάλ η απήχηση μειώθηκε κατά **{drop:.0%}** — "
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
