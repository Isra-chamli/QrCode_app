import streamlit as st
import pandas as pd
from auth import exige_connexion
from config import SEUIL_STOCK_FAIBLE

st.set_page_config(page_title="Maklada - QR Traçabilité", page_icon="🏷️", layout="wide")
exige_connexion()

DATA_PATH = "data/stock_maklada.csv"

@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH)

df = load_data()

st.title("🏷️ Maklada - Traçabilité par QR Code")
st.caption("Données réelles issues de l'export Dynamics AX")

seuil = st.sidebar.number_input(
    "⚠️ Seuil de stock faible", min_value=0, value=SEUIL_STOCK_FAIBLE, step=10
)

df["stock_faible"] = df["Stock physique"] < seuil

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Lignes de stock", len(df))
col2.metric("Articles distincts", df["Numéro d'article"].nunique())
col3.metric("Entrepôts", df["Entrepôt"].nunique())
col4.metric("Stock physique total", f"{df['Stock physique'].sum():,.0f}".replace(",", " "))
col5.metric("🔴 Lignes en stock faible", int(df["stock_faible"].sum()))

st.divider()

tab1, tab2 = st.tabs(["📋 Tout le stock", "🔴 Stock faible uniquement"])

with tab1:
    entrepot_filtre = st.selectbox(
        "Filtrer par entrepôt", ["Tous"] + sorted(df["Entrepôt"].dropna().unique().tolist())
    )
    df_affiche = df if entrepot_filtre == "Tous" else df[df["Entrepôt"] == entrepot_filtre]
    st.dataframe(df_affiche.head(200), use_container_width=True, hide_index=True)
    st.caption(f"{len(df_affiche)} lignes correspondantes (200 premières affichées)")

with tab2:
    df_faible = df[df["stock_faible"]]
    if df_faible.empty:
        st.success("Aucune ligne sous le seuil défini.")
    else:
        st.warning(f"{len(df_faible)} ligne(s) sous le seuil de {seuil}.")
        st.dataframe(df_faible, use_container_width=True, hide_index=True)

st.divider()
st.info(
    "➡️ **Génerer QR Code** : créer une étiquette QR imprimable pour une ligne de stock.\n\n"
    "➡️ **Scanner / Rechercher** : uploader une photo d'étiquette QR pour retrouver la fiche produit.\n\n"
    "➡️ **Génération en masse** : créer plusieurs étiquettes (ZIP) ou une planche PDF imprimable."
)