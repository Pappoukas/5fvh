"""
Chania Book Festival — Social Media Analytics Dashboard
Streamlit app για ανάλυση της επικοινωνιακής στρατηγικής social media
του 5ου Φεστιβάλ Βιβλίου Χανίων (Instagram Stories, Facebook, Instagram Feed).
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from wordcloud import WordCloud

from utils.data_loader import load_all, FESTIVAL_START, FESTIVAL_END

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
st.plotly_chart(fig, use_container_width=True)

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
    st.plotly_chart(fig_ch, use_container_width=True)

with col_right:
    st.subheader("🎞️ Απόδοση ανά τύπο περιεχομένου")
    fmt = owned.groupby("format").agg(
        posts=("id", "count"), avg_reach=("reach", "mean")
    ).reset_index().sort_values("avg_reach", ascending=False)
    fig_fmt = px.bar(fmt, x="format", y="avg_reach", text="posts",
                      labels={"avg_reach": "Μέση απήχηση/post", "format": "Τύπος"})
    fig_fmt.update_traces(texttemplate="n=%{text}", textposition="outside")
    st.plotly_chart(fig_fmt, use_container_width=True)

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
st.plotly_chart(fig_heat, use_container_width=True)

st.markdown("---")

# ----------------------------------------------------------- TOP POSTS ---
st.subheader("🏆 Top 10 δημοσιεύσεις (δικές μας) ανά απήχηση")
top = owned.nlargest(10, "reach")[["dt", "channel", "format", "text", "reach", "engagement", "link"]].copy()
top["text"] = top["text"].str.slice(0, 90) + "…"
top["dt"] = top["dt"].dt.strftime("%d/%m/%Y %H:%M")
st.dataframe(top, use_container_width=True, hide_index=True)

st.markdown("---")

# -------------------------------------------------------- EARNED MEDIA ---
st.subheader("🤝 Earned media — ποιοι μας ανέφεραν")
if len(earned):
    em = earned.groupby("account").agg(mentions=("id", "count")).reset_index().sort_values(
        "mentions", ascending=False
    )
    fig_em = px.bar(em, x="account", y="mentions", labels={"account": "Λογαριασμός", "mentions": "Αναφορές"})
    st.plotly_chart(fig_em, use_container_width=True)
    st.caption(
        "Το Meta δεν παρέχει δεδομένα απήχησης/engagement για δημοσιεύσεις τρίτων λογαριασμών — "
        "μετράμε μόνο τον αριθμό αναφορών/tags."
    )
else:
    st.info("Δεν υπάρχουν καταγεγραμμένες αναφορές τρίτων στο επιλεγμένο εύρος.")

st.markdown("---")

# ------------------------------------------------------- STORY METRICS ---
st.subheader("📱 Ανάλυση Instagram Stories (μόνο δικές μας)")
stories = owned[owned["format"] == "Story"]
if len(stories):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Σύνολο Link Clicks", int(stories["link_clicks"].sum()))
    c2.metric("Σύνολο Profile Visits", int(stories["profile_visits"].sum()))
    c3.metric("Σύνολο Replies", int(stories["replies"].sum()))
    c4.metric("Σύνολο Sticker Taps", int(stories["sticker_taps"].sum()))

    story_timeline = stories.groupby("date")[["link_clicks", "profile_visits"]].sum().reset_index()
    fig_story = px.line(story_timeline, x="date", y=["link_clicks", "profile_visits"],
                        labels={"value": "Αριθμός", "variable": "Μετρική"})
    st.plotly_chart(fig_story, use_container_width=True)

    top_stories = stories.nlargest(5, "link_clicks")[["dt", "text", "link_clicks", "profile_visits"]]
    top_stories["text"] = top_stories["text"].str.slice(0, 80) + "…"
    top_stories["dt"] = top_stories["dt"].dt.strftime("%d/%m %H:%M")
    st.dataframe(top_stories, use_container_width=True, hide_index=True)
else:
    st.info("Δεν υπάρχουν δικές μας Instagram Stories στο επιλεγμένο εύρος.")

# ---------------------------------------------------------- WORD CLOUD ---
st.markdown("---")
st.subheader("☁️ Word Cloud από τα κείμενα των δικών μας δημοσιεύσεων")
if len(owned) > 0:
    all_text = " ".join(owned["text"].dropna().astype(str))
    wordcloud = WordCloud(width=800, height=400, background_color="white",
                          max_words=100, colormap="Oranges",
                          stopwords={"της", "και", "στο", "για", "να", "με", "από", "την", "τους", "που", "θα", "στο", "στην"}).generate(all_text)

    fig_wc, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation="bilinear")
    ax.axis("off")
    st.pyplot(fig_wc)
else:
    st.info("Δεν υπάρχουν κείμενα για ανάλυση.")

# --------------------------------------------------- SPEAKER ANALYSIS ---
st.markdown("---")
st.subheader("🎤 Ανάλυση Ομιλητών / Συγγραφέων (μόνο δικές μας)")
speaker_list = []
for _, row in owned.iterrows():
    for sp in row["speakers"]:
        speaker_list.append({
            "speaker": sp,
            "reach": row["reach"],
            "engagement": row["engagement"],
            "posts": 1
        })
if speaker_list:
    sp_df = pd.DataFrame(speaker_list)
    sp_agg = sp_df.groupby("speaker").agg(
        total_reach=("reach", "sum"),
        total_engagement=("engagement", "sum"),
        mentions=("posts", "count")
    ).reset_index().sort_values("total_reach", ascending=False)

    top_speakers = sp_agg.head(10)
    fig_sp = px.bar(top_speakers, x="speaker", y="total_reach",
                    text="mentions", labels={"total_reach": "Συνολική απήχηση", "speaker": ""})
    fig_sp.update_traces(texttemplate="%{text} posts", textposition="outside")
    st.plotly_chart(fig_sp, use_container_width=True)

    st.dataframe(top_speakers, use_container_width=True, hide_index=True)
else:
    st.info("Δεν εντοπίστηκαν ονόματα ομιλητών στα κείμενα.")

# ----------------------------------------------- CONTENT CATEGORIES ---
st.markdown("---")
st.subheader("📂 Απόδοση ανά κατηγορία περιεχομένου (δικές μας)")
cat_agg = owned.groupby("content_category").agg(
    posts=("id", "count"),
    total_reach=("reach", "sum"),
    avg_reach=("reach", "mean"),
    engagement=("engagement", "sum")
).reset_index().sort_values("total_reach", ascending=False)

fig_cat = px.bar(cat_agg, x="content_category", y="total_reach",
                 text="posts", labels={"total_reach": "Συνολική απήχηση", "content_category": "Κατηγορία"})
fig_cat.update_traces(texttemplate="%{text} posts", textposition="outside")
st.plotly_chart(fig_cat, use_container_width=True)

# ----------------------------------------------------- NEGATIVE FEEDBACK ---
st.markdown("---")
st.subheader("👎 Αρνητικά σχόλια (Facebook: αποκρύψεις)")
fb_owned = owned[owned["channel"] == "Facebook"]
if len(fb_owned) > 0 and fb_owned["hides"].sum() > 0:
    hide_agg = fb_owned.groupby("phase")["hides"].sum().reset_index()
    fig_hide = px.bar(hide_agg, x="phase", y="hides", labels={"hides": "Σύνολο αποκρύψεων", "phase": "Φάση"})
    st.plotly_chart(fig_hide, use_container_width=True)
    st.caption("Οι αποκρύψεις είναι ένδειξη ότι το περιεχόμενο δεν αρέσει σε κάποιους χρήστες.")
else:
    st.info("Δεν υπάρχουν αρνητικά σχόλια (αποκρύψεις) στα επιλεγμένα δεδομένα.")

# --------------------------------------------------------- STRATEGY ----
st.markdown("---")
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
