import streamlit as st
import pandas as pd
import io
import zipfile
from auth import exige_connexion
from labels import generer_etiquette, nom_fichier_etiquette

st.set_page_config(page_title="Génération en masse", page_icon="📦", layout="centered")
exige_connexion()

DATA_PATH = "data/stock_maklada.csv"

@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH)

df = load_data()

st.title("📦 Génération d'étiquettes en masse")
st.write("Génère toutes les étiquettes d'un entrepôt (ou d'une recherche) en un seul ZIP.")

mode = st.radio("Filtrer par", ["Entrepôt", "Recherche texte"], horizontal=True)

if mode == "Entrepôt":
    entrepot = st.selectbox("Entrepôt", sorted(df["Entrepôt"].dropna().unique().tolist()))
    lignes = df[df["Entrepôt"] == entrepot]
else:
    terme = st.text_input("Recherche (article, désignation ou lot)")
    if terme:
        lignes = df[
            df["Numéro d'article"].str.contains(terme, case=False, na=False)
            | df["Nom du produit"].str.contains(terme, case=False, na=False)
            | df["Numéro du lot"].astype(str).str.contains(terme, case=False, na=False)
        ]
    else:
        lignes = df.head(0)

st.write(f"**{len(lignes)}** ligne(s) correspondante(s).")

if len(lignes) > 300:
    st.warning("Plus de 300 lignes sélectionnées — la génération peut prendre du temps.")

if not lignes.empty:
    st.dataframe(
        lignes[["Numéro d'article", "Nom du produit", "Numéro du lot", "Emplacement", "Entrepôt"]].head(50),
        use_container_width=True, hide_index=True
    )
    if len(lignes) > 50:
        st.caption(f"Aperçu limité à 50 lignes — les {len(lignes)} étiquettes seront générées dans le ZIP.")

    if st.button(f"🏷️ Générer {len(lignes)} étiquette(s) (ZIP)"):
        with st.spinner("Génération en cours..."):
            buf_zip = io.BytesIO()
            with zipfile.ZipFile(buf_zip, "w", zipfile.ZIP_DEFLATED) as zf:
                noms_utilises = set()
                for _, produit in lignes.iterrows():
                    label = generer_etiquette(produit)
                    nom = nom_fichier_etiquette(produit)
                    # éviter les doublons de nom de fichier
                    base_nom = nom
                    compteur = 1
                    while nom in noms_utilises:
                        nom = base_nom.replace(".png", f"_{compteur}.png")
                        compteur += 1
                    noms_utilises.add(nom)

                    img_buf = io.BytesIO()
                    label.save(img_buf, format="PNG")
                    zf.writestr(nom, img_buf.getvalue())

            st.success(f"{len(lignes)} étiquette(s) générée(s).")
            st.download_button(
                "⬇️ Télécharger le ZIP",
                data=buf_zip.getvalue(),
                file_name="etiquettes_maklada.zip",
                mime="application/zip"
            )