# app.py (προσθήκες μετά την ενότητα "Αυτόματα strategic insights")

# … (υπάρχων κώδικας μέχρι το στρατηγικά insights)

# ------------------------------------------------------- STORY METRICS ---
st.markdown("---")
st.subheader("📱 Ανάλυση Instagram Stories (μόνο δικές μας)")
stories = owned[owned["format"] == "Story"]
if len(stories):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Σύνολο Link Clicks", int(stories["link_clicks"].sum()))
    c2.metric("Σύνολο Profile Visits", int(stories["profile_visits"].sum()))
    c3.metric("Σύνολο Replies", int(stories["replies"].sum()))
    c4.metric("Σύνολο Sticker Taps", int(stories["sticker_taps"].sum()))

    # Γράφημα εξέλιξης link clicks
    story_timeline = stories.groupby("date")[["link_clicks", "profile_visits"]].sum().reset_index()
    fig_story = px.line(story_timeline, x="date", y=["link_clicks", "profile_visits"],
                        labels={"value": "Αριθμός", "variable": "Μετρική"})
    st.plotly_chart(fig_story, use_container_width=True)

    # Top 5 stories με τα περισσότερα link clicks
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
    from wordcloud import WordCloud
    import matplotlib.pyplot as plt

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
# Επεκτείνουμε τον πίνακα με τους ομιλητές
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

    # Πίνακας με αναλυτικά στοιχεία
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

# --------------------------------------------------------- FOOTER ---
st.markdown("---")
st.caption("Dashboard ενημερώθηκε με βάση τα δεδομένα Meta Business Suite.")
