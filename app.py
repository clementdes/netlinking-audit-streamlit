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

else:
    st.info("📄 Veuillez uploader un ou deux fichiers CSV contenant vos backlinks pour commencer l'analyse.")
