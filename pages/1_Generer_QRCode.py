import streamlit as st
import pandas as pd
import io
from auth import exige_connexion
from config import SEUIL_STOCK_FAIBLE
from labels import generer_etiquette, nom_fichier_etiquette

st.set_page_config(page_title="Générer QR Code", page_icon="🏷️", layout="centered")
exige_connexion()

DATA_PATH = "data/stock_maklada.csv"

@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH)

df = load_data()

st.title("🏷️ Générer une étiquette QR Code")

st.write("Recherche une ligne de stock (article, désignation ou lot) pour générer son étiquette.")
recherche = st.text_input("Rechercher", placeholder="ex: AAB-BC, ACIER, OF26-0101")

if recherche:
    resultats = df[
        df["Numéro d'article"].str.contains(recherche, case=False, na=False)
        | df["Nom du produit"].str.contains(recherche, case=False, na=False)
        | df["Numéro du lot"].astype(str).str.contains(recherche, case=False, na=False)
    ]
else:
    resultats = df.head(50)

if resultats.empty:
    st.warning("Aucun résultat.")
    st.stop()

def format_choix(i):
    ligne = df.loc[df["id"] == i].iloc[0]
    article = ligne["Numéro d'article"]
    lot = ligne["Numéro du lot"]
    emplacement = ligne["Emplacement"]
    entrepot = ligne["Entrepôt"]
    badge = " 🔴" if ligne["Stock physique"] < SEUIL_STOCK_FAIBLE else ""
    return f"{article} | Lot {lot} | Emp. {emplacement} | {entrepot}{badge}"

choix = st.selectbox("Choisir la ligne de stock", resultats["id"], format_func=format_choix)

produit = df[df["id"] == choix].iloc[0]

if produit["Stock physique"] < SEUIL_STOCK_FAIBLE:
    st.warning(f"⚠️ Stock faible : {produit['Stock physique']:,.0f} unités (seuil {SEUIL_STOCK_FAIBLE})")

label = generer_etiquette(produit)
st.image(label, caption="Aperçu de l'étiquette", use_container_width=False)

buf = io.BytesIO()
label.save(buf, format="PNG")
st.download_button(
    "⬇️ Télécharger l'étiquette (PNG)",
    data=buf.getvalue(),
    file_name=nom_fichier_etiquette(produit),
    mime="image/png"
)

with st.expander("Détails complets de la ligne"):
    st.json(produit.to_dict())