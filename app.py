import streamlit as st
import pandas as pd

st.set_page_config(page_title="Maklada - QR Traçabilité", page_icon="🏷️", layout="wide")

DATA_PATH = "data/stock_maklada.csv"

@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH)

df = load_data()

st.title("🏷️ Maklada - Traçabilité par QR Code")
st.caption("Données réelles issues de l'export Dynamics AX")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Lignes de stock", len(df))
col2.metric("Articles distincts", df["Numéro d'article"].nunique())
col3.metric("Entrepôts", df["Entrepôt"].nunique())
col4.metric("Stock physique total", f"{df['Stock physique'].sum():,.0f}".replace(",", " "))

st.divider()
st.subheader("📋 Aperçu du stock")

entrepot_filtre = st.selectbox("Filtrer par entrepôt", ["Tous"] + sorted(df["Entrepôt"].dropna().unique().tolist()))
df_affiche = df if entrepot_filtre == "Tous" else df[df["Entrepôt"] == entrepot_filtre]

st.dataframe(df_affiche.head(200), use_container_width=True, hide_index=True)
st.caption(f"{len(df_affiche)} lignes correspondantes (200 premières affichées)")

st.divider()
st.info(
    "➡️ **Génerer QR Code** : créer une étiquette QR imprimable pour une ligne de stock (article + lot).\n\n"
    "➡️ **Scanner / Rechercher** : uploader une photo d'étiquette QR pour retrouver la fiche produit."
)