import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from io import StringIO

st.set_page_config(page_title="Audit Netlinking", layout="wide")
st.markdown("""
    <style>
        .main {background-color: #f8f9fa;}
        .block-container {padding-top: 2rem;}
        h1, h2, h3, h4 {color: #333333;}
        .stMetric {background-color: #ffffff; padding: 1rem; border-radius: 8px;}
    </style>
""", unsafe_allow_html=True)

st.title("🔗 Audit de Netlinking SEO")
st.caption("Importe ton fichier CSV pour analyser les backlinks de ton site")

# Upload CSV
uploaded_file = st.file_uploader("📁 Charger un fichier de backlinks (.csv)", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip()

    # Convertir champs numériques
    for col in ['Domain rating', 'Domain traffic', 'UR']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Convertir dates
    for col in ['First seen', 'Last seen']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    st.success("✅ Fichier chargé avec succès !")

    # Layout global en colonnes
    col1, col2, col3 = st.columns(3)
    col1.metric("🔗 Total backlinks", len(df))
    col2.metric("🌐 Domaines référents", df['Referring page URL'].nunique())
    if 'Domain rating' in df.columns:
        mean_dr = df['Domain rating'].mean()
        col3.metric("📊 DR moyen", round(mean_dr, 2))

    st.markdown("---")
    st.subheader("📊 Aperçu des données principales")
    st.dataframe(df[['Referring page URL', 'Target URL', 'Anchor', 'Domain rating', 'First seen', 'Last seen']].head(10))

    with st.expander("🔎 Filtrer les données avancées"):
        min_dr = st.slider("Filtrer par Domain Rating minimum", 0, 100, 10)
        df = df[df['Domain rating'] >= min_dr]

    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["📅 Historique", "📝 Ancres", "🌍 Domaines"])

    with tab1:
        st.subheader("Évolution des backlinks")
        if 'First seen' in df.columns:
            df_month = df.dropna(subset=['First seen']).copy()
            df_month['Month'] = df_month['First seen'].dt.to_period("M").astype(str)
            monthly_links = df_month.groupby('Month').size().reset_index(name='Nouveaux backlinks')
            fig = px.area(monthly_links, x='Month', y='Nouveaux backlinks', title="Backlinks créés par mois")
            st.plotly_chart(fig, use_container_width=True)

        if 'Last seen' in df.columns:
            lost_df = df.dropna(subset=['Last seen']).copy()
            lost_df['Month'] = lost_df['Last seen'].dt.to_period("M").astype(str)
            lost_links = lost_df.groupby('Month').size().reset_index(name='Backlinks perdus')
            fig2 = px.area(lost_links, x='Month', y='Backlinks perdus', title="Backlinks perdus par mois")
            st.plotly_chart(fig2, use_container_width=True)

    with tab2:
        st.subheader("Typologie des ancres")
        branding = "waalaxy"
        domain = "waalaxy.com"
        anchor_col = df['Anchor'].fillna('').str.lower()

        def categorize_anchor(anchor):
            if "http" in anchor:
                return "URL"
            elif branding in anchor:
                return "Branding"
            elif domain in anchor:
                return "Nom de domaine"
            elif anchor.strip() in ["cliquez ici", "voir plus", "lire l'article"]:
                return "Générique"
            elif anchor.strip() == "" or pd.isna(anchor):
                return "Vide"
            elif len(anchor.strip().split()) <= 2:
                return "Exact match"
            else:
                return "Optimisée"

        df['Anchor Type'] = anchor_col.apply(categorize_anchor)
        anchor_stats = df['Anchor Type'].value_counts().reset_index()
        anchor_stats.columns = ['Type', 'Nombre']
        fig3 = px.pie(anchor_stats, names='Type', values='Nombre', title="Répartition des types d'ancres")
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown("Top 10 ancres les plus fréquentes :")
        st.dataframe(df['Anchor'].value_counts().head(10))

    with tab3:
        st.subheader("Top domaines référents")
        top_domains = df.groupby('Referring page URL').agg({
            'Domain rating': 'mean',
            'Domain traffic': 'mean',
            'Anchor': 'count'
        }).sort_values(by='Anchor', ascending=False).head(10).reset_index()
        top_domains.columns = ['Referring page URL', 'DR moyen', 'Trafic moyen', 'Nombre de backlinks']
        st.dataframe(top_domains)
        fig4 = px.bar(top_domains, x='Referring page URL', y='Nombre de backlinks',
                     title="Top 10 domaines référents par volume de liens")
        st.plotly_chart(fig4, use_container_width=True)

else:
    st.info("📄 Veuillez uploader un fichier CSV contenant vos backlinks pour commencer l'analyse.")
