import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from io import StringIO
import datetime

st.set_page_config(page_title="Analyse Netlinking", layout="wide")
st.title("🧬 Dashboard d'analyse de Netlinking")

# Upload CSV
uploaded_file = st.file_uploader("Upload your backlinks CSV", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip()

    # Convert numeric fields explicitly
    if 'Domain rating' in df.columns:
        df['Domain rating'] = pd.to_numeric(df['Domain rating'], errors='coerce')

    # Parse dates
    if 'First seen' in df.columns:
        df['First seen'] = pd.to_datetime(df['First seen'], errors='coerce')
    if 'Last seen' in df.columns:
        df['Last seen'] = pd.to_datetime(df['Last seen'], errors='coerce')

    st.subheader("Aperçu des données")
    st.dataframe(df.head(10))

    tabs = st.tabs(["Vue d'ensemble", "Ancres", "Qualité des liens", "Pages linkées", "Domaines", "Historique"])

    # Tab 1: Vue d'ensemble
    with tabs[0]:
        st.header("Vue d'ensemble")
        st.metric("Nombre total de backlinks", len(df))
        st.metric("Nombre de domaines référents uniques", df['Referring page URL'].nunique())

        if 'Domain rating' in df.columns:
            mean_dr = df['Domain rating'].mean()
            if pd.notna(mean_dr):
                st.metric("Domain Rating moyen", round(mean_dr, 2))

        if 'First seen' in df.columns:
            df_month = df.dropna(subset=['First seen']).copy()
            df_month['Month'] = df_month['First seen'].dt.to_period("M").astype(str)
            monthly_links = df_month.groupby('Month').size().reset_index(name='Backlinks')
            fig = px.line(monthly_links, x='Month', y='Backlinks', title="Backlinks créés par mois")
            st.plotly_chart(fig, use_container_width=True)

    # Tab 2: Analyse des ancres
    with tabs[1]:
        st.header("Analyse des ancres")
        anchor_col = df['Anchor'].fillna('').str.lower()
        branding = "waalaxy"
        domain = "waalaxy.com"

        def categorize_anchor(anchor):
            if "http" in anchor:
                return "URL"
            elif branding in anchor:
                return "Branding"
            elif domain in anchor:
                return "Nom de domaine"
            elif anchor in ["cliquez ici", "voir plus", "lire l'article"]:
                return "Générique"
            elif anchor == "" or pd.isna(anchor):
                return "Vide"
            elif len(anchor.split()) <= 2:
                return "Exact match"
            else:
                return "Optimisée"

        df['Anchor Type'] = anchor_col.apply(categorize_anchor)
        anchor_counts = df['Anchor Type'].value_counts().reset_index()
        anchor_counts.columns = ['Type', 'Nombre']
        fig = px.pie(anchor_counts, names='Type', values='Nombre', title="Répartition des types d'ancres")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df['Anchor'].value_counts().head(20))

    # Tab 3: Qualité des liens
    with tabs[2]:
        st.header("Qualité des liens")
        if 'Domain rating' in df.columns:
            fig, ax = plt.subplots()
            ax.hist(df['Domain rating'].dropna(), bins=20, color='skyblue', edgecolor='black')
            ax.set_title("Distribution du Domain Rating")
            st.pyplot(fig)

        for col in ['Nofollow', 'UGC', 'Sponsored']:
            if col in df.columns:
                st.metric(f"{col} links", df[col].sum())

        if 'Referring page HTTP code' in df.columns:
            code_counts = df['Referring page HTTP code'].value_counts().reset_index()
            code_counts.columns = ['HTTP Code', 'Nombre']
            fig = px.bar(code_counts, x='HTTP Code', y='Nombre', title="Codes HTTP des pages référentes")
            st.plotly_chart(fig, use_container_width=True)

    # Tab 4: Pages les plus linkées
    with tabs[3]:
        st.header("Pages internes les plus linkées")
        if 'Target URL' in df.columns:
            top_targets = df['Target URL'].value_counts().head(10).reset_index()
            top_targets.columns = ['Target URL', 'Nombre de backlinks']
            fig = px.bar(top_targets, x='Target URL', y='Nombre de backlinks', title="Top 10 pages les plus linkées")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(top_targets)

    # Tab 5: Domaines référents
    with tabs[4]:
        st.header("Domaines référents")
        if 'Domain rating' in df.columns and 'Referring page URL' in df.columns:
            df['Domain rating'] = pd.to_numeric(df['Domain rating'], errors='coerce')
            df['Domain traffic'] = pd.to_numeric(df['Domain traffic'], errors='coerce')
            top_domains = df.groupby('Referring page URL').agg({
                'Domain rating': 'mean',
                'Domain traffic': 'mean',
                'Anchor': 'count'
            }).sort_values(by='Anchor', ascending=False).head(10).reset_index()
            fig = px.bar(top_domains, x='Referring page URL', y='Anchor', title="Top 10 domaines en nombre de backlinks")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(top_domains)

    # Tab 6: Historique
    with tabs[5]:
        st.header("Historique des backlinks")
        if 'First seen' in df.columns and 'Last seen' in df.columns:
            df['Month'] = df['First seen'].dt.to_period("M").astype(str)
            new_links = df.groupby('Month').size().reset_index(name='Nouveaux liens')
            fig = px.bar(new_links, x='Month', y='Nouveaux liens', title="Nouveaux backlinks par mois")
            st.plotly_chart(fig, use_container_width=True)

            lost_links = df.dropna(subset=['Last seen'])
            lost_links['Month'] = lost_links['Last seen'].dt.to_period("M").astype(str)
            lost = lost_links.groupby('Month').size().reset_index(name='Liens perdus')
            fig = px.bar(lost, x='Month', y='Liens perdus', title="Backlinks perdus par mois")
            st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Veuillez uploader un fichier CSV pour commencer.")
