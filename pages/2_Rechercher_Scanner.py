import streamlit as st
import pandas as pd
import numpy as np
import cv2
from PIL import Image

st.set_page_config(page_title="Scanner / Rechercher", page_icon="🔎", layout="centered")

DATA_PATH = "data/stock_maklada.csv"

@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH)

df = load_data()

st.title("🔎 Scanner / Rechercher une ligne de stock")

tab1, tab2 = st.tabs(["📷 Scanner une étiquette", "🔤 Recherche manuelle"])

def val(x, default="-"):
    return default if pd.isna(x) else x

def afficher_fiche(produit):
    st.success("Ligne de stock trouvée ✅")

    article = produit["Numéro d'article"]
    designation = val(produit["Nom du produit"])
    lot = val(produit["Numéro du lot"])
    emplacement = val(produit["Emplacement"])
    entrepot = val(produit["Entrepôt"])
    site = val(produit["Site"])
    stock = val(produit["Stock physique"])
    stock_str = f"{stock:,.0f}".replace(",", " ") if not isinstance(stock, str) else stock
    ligne_id = produit["id"]

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**Article :** {article}")
        st.markdown(f"**Désignation :** {designation}")
        st.markdown(f"**Lot :** {lot}")
        st.markdown(f"**Emplacement :** {emplacement}")
    with c2:
        st.markdown(f"**Entrepôt :** {entrepot}")
        st.markdown(f"**Site :** {site}")
        st.markdown(f"**Stock physique :** {stock_str}")
        st.markdown(f"**ID ligne :** {ligne_id}")

with tab1:
    st.write("Prends en photo ou uploade l'étiquette contenant le QR Code.")
    photo = st.camera_input("Prendre une photo") or st.file_uploader(
        "Ou uploader une image", type=["png", "jpg", "jpeg"]
    )

    if photo is not None:
        image = Image.open(photo).convert("RGB")
        img_array = np.array(image)
        img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

        detector = cv2.QRCodeDetector()
        data, points, _ = detector.detectAndDecode(img_cv)

        if data:
            st.write(f"Contenu détecté : `{data}`")
            if data.startswith("MAKLADA-ID:"):
                ligne_id = int(data.split(":")[1])
                match = df[df["id"] == ligne_id]
                if not match.empty:
                    afficher_fiche(match.iloc[0])
                else:
                    st.error("QR Code reconnu mais ligne introuvable dans la base.")
            else:
                st.warning("QR Code non reconnu (format inattendu).")
        else:
            st.error("Aucun QR Code détecté dans l'image. Réessaie avec une photo plus nette.")

with tab2:
    recherche = st.text_input("Article, désignation ou lot")
    if recherche:
        resultats = df[
            df["Numéro d'article"].str.contains(recherche, case=False, na=False)
            | df["Nom du produit"].str.contains(recherche, case=False, na=False)
            | df["Numéro du lot"].astype(str).str.contains(recherche, case=False, na=False)
        ]
        if not resultats.empty:
            st.caption(f"{len(resultats)} résultat(s) — 20 premiers affichés")
            for _, produit in resultats.head(20).iterrows():
                with st.container(border=True):
                    afficher_fiche(produit)
        else:
            st.warning("Aucun résultat.")