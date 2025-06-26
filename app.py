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
st.caption("Importe un ou deux fichiers CSV pour analyser et comparer les backlinks de ton site")

# Upload CSVs
uploaded_files = st.file_uploader("📁 Charger un ou deux fichiers de backlinks (.csv)", type=["csv"], accept_multiple_files=True)

if uploaded_files:
    dfs = []
    for uploaded_file in uploaded_files:
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip()

        for col in ['Domain rating', 'Domain traffic', 'UR']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        for col in ['First seen', 'Last seen']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        dfs.append(df)

    df = dfs[0]  # base dataframe
    st.success("✅ Fichier principal chargé avec succès !")

    # Metrics display
    col1, col2, col3 = st.columns(3)
    col1.metric("🔗 Total backlinks", len(df))
    col2.metric("🌐 Domaines référents", df['Referring page URL'].nunique())
    if 'Domain rating' in df.columns:
        mean_dr = df['Domain rating'].mean()
        col3.metric("📊 DR moyen", round(mean_dr, 2))

    st.markdown("---")
    st.subheader("📊 Répartition des backlinks par tranche de Domain Rating")

    bins = [0, 29, 44, 59, 100]
    labels = ["DR 0-29", "DR 30-44", "DR 45-59", "DR 60-100"]
    df['DR Range'] = pd.cut(df['Domain rating'], bins=bins, labels=labels, right=True, include_lowest=True)
    dr_table = df['DR Range'].value_counts().sort_index().reset_index()
    dr_table.columns = ['Tranche DR', 'Nombre de backlinks']
    st.dataframe(dr_table)
    fig_dr = px.bar(dr_table, x='Tranche DR', y='Nombre de backlinks', title="Backlinks par tranche de Domain Rating")
    st.plotly_chart(fig_dr, use_container_width=True)

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
    anchor = anchor.strip()
    if anchor == "" or pd.isna(anchor):
        return "Vide"
    if "http" in anchor:
        return "URL"
    if branding in anchor:
        return "Branding"
    if domain in anchor:
        return "Nom de domaine"
    if anchor in ["cliquez ici", "voir plus", "lire l'article", "en savoir plus", "ici"]:
        return "Générique"
    # Exact match : simulate keyword extraction from target
    if anchor in df['Target URL'].astype(str).str.lower().apply(lambda url: url.split('/')[-1] if '/' in url else url):
        return "Exact match"
    if any(anchor in url.lower() for url in df['Target URL'].astype(str)):
        return "Optimisée"
    return "Autre"

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

    # Comparaison
    if len(dfs) == 2:
        st.markdown("---")
        st.subheader("🔁 Comparaison entre les deux fichiers")

        df1 = dfs[0]
        df2 = dfs[1]

        st.write("Fichier 1 :", uploaded_files[0].name)
        st.write("Fichier 2 :", uploaded_files[1].name)

        comp1 = len(df1)
        comp2 = len(df2)

        delta_links = comp2 - comp1
        delta_domains = df2['Referring page URL'].nunique() - df1['Referring page URL'].nunique()

        col_a, col_b = st.columns(2)
        col_a.metric("Backlinks", comp1, delta=delta_links)
        col_b.metric("Domaines référents", df1['Referring page URL'].nunique(), delta=delta_domains)

        if 'Domain rating' in df1.columns and 'Domain rating' in df2.columns:
            dr1 = round(df1['Domain rating'].mean(), 2)
            dr2 = round(df2['Domain rating'].mean(), 2)
            st.metric("DR moyen", dr1, delta=round(dr2 - dr1, 2))

            st.subheader("📊 Répartition comparative par tranche de DR")
            df1['DR Range'] = pd.cut(df1['Domain rating'], bins=bins, labels=labels, right=True, include_lowest=True)
            df2['DR Range'] = pd.cut(df2['Domain rating'], bins=bins, labels=labels, right=True, include_lowest=True)

            dr_comp1 = df1['DR Range'].value_counts().sort_index().reset_index()
            dr_comp1.columns = ['Tranche DR', 'Fichier 1']
            dr_comp2 = df2['DR Range'].value_counts().sort_index().reset_index()
            dr_comp2.columns = ['Tranche DR', 'Fichier 2']

            dr_comp1['Tranche DR'] = dr_comp1['Tranche DR'].astype(str)
dr_comp2['Tranche DR'] = dr_comp2['Tranche DR'].astype(str)
dr_compare = pd.merge(dr_comp1, dr_comp2, on='Tranche DR', how='outer').fillna(0)
            st.dataframe(dr_compare)
            fig_comp = px.bar(dr_compare.melt(id_vars='Tranche DR', var_name='Fichier', value_name='Backlinks'),
                              x='Tranche DR', y='Backlinks', color='Fichier', barmode='group',
                              title="Comparaison des backlinks par tranche de DR")
            st.plotly_chart(fig_comp, use_container_width=True)

else:
    st.info("📄 Veuillez uploader un ou deux fichiers CSV contenant vos backlinks pour commencer l'analyse.")
