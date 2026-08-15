import streamlit as st
import numpy as np
import cv2
from PIL import Image
from db import get_ligne, rechercher_stock, enregistrer_mouvement, enregistrer_scan, historique_ligne

st.set_page_config(page_title="Scanner / Rechercher", page_icon="🔎", layout="centered")

st.title("🔎 Scanner / Rechercher une ligne de stock")

tab1, tab2 = st.tabs(["📷 Scanner une étiquette", "🔤 Recherche manuelle"])

def val(x, default="-"):
    return default if x is None else x

def afficher_fiche(produit, cle_suffix=""):
    """produit est un dict (issu de get_ligne ou d'une ligne de résultats)."""
    st.success("Ligne de stock trouvée ✅")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**Article :** {produit['article']}")
        st.markdown(f"**Désignation :** {val(produit['designation'])}")
        st.markdown(f"**Lot :** {val(produit['lot'])}")
        st.markdown(f"**Emplacement :** {val(produit['emplacement'])}")
    with c2:
        st.markdown(f"**Entrepôt :** {val(produit['entrepot'])}")
        st.markdown(f"**Site :** {val(produit['site'])}")
        stock = val(produit["stock_physique"])
        stock_str = f"{stock:,.0f}".replace(",", " ") if not isinstance(stock, str) else stock
        st.markdown(f"**Stock physique :** {stock_str}")
        st.markdown(f"**ID ligne :** {produit['id']}")

    # --- Enregistrement de mouvement ---
    with st.expander("📦 Enregistrer un mouvement de stock"):
        with st.form(key=f"mvt_form_{produit['id']}_{cle_suffix}"):
            type_mvt = st.radio("Type", ["sortie", "entree"], horizontal=True, key=f"type_{produit['id']}_{cle_suffix}")
            quantite = st.number_input("Quantité", min_value=0.0, step=1.0, key=f"qte_{produit['id']}_{cle_suffix}")
            utilisateur = st.text_input("Ton nom", key=f"user_{produit['id']}_{cle_suffix}")
            valider = st.form_submit_button("Valider le mouvement")
            if valider:
                if quantite <= 0:
                    st.error("Indique une quantité supérieure à 0.")
                elif type_mvt == "sortie" and quantite > (produit["stock_physique"] or 0):
                    st.error("Quantité supérieure au stock disponible.")
                else:
                    enregistrer_mouvement(produit["id"], type_mvt, quantite, utilisateur or "inconnu")
                    st.success(f"Mouvement enregistré : {type_mvt} de {quantite}. Rafraîchis la page pour voir le nouveau stock.")

    # --- Historique ---
    with st.expander("🕓 Historique de cette ligne"):
        mouvements, scans = historique_ligne(produit["id"])
        st.write("**Mouvements**")
        if mouvements.empty:
            st.caption("Aucun mouvement enregistré.")
        else:
            st.dataframe(mouvements, use_container_width=True, hide_index=True)
        st.write("**Scans**")
        if scans.empty:
            st.caption("Aucun scan enregistré.")
        else:
            st.dataframe(scans, use_container_width=True, hide_index=True)

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
                produit = get_ligne(ligne_id)
                if produit:
                    enregistrer_scan(ligne_id, action="scan_qr")
                    afficher_fiche(produit, cle_suffix="scan")
                else:
                    st.error("QR Code reconnu mais ligne introuvable dans la base.")
            else:
                st.warning("QR Code non reconnu (format inattendu).")
        else:
            st.error("Aucun QR Code détecté dans l'image. Réessaie avec une photo plus nette.")

with tab2:
    recherche = st.text_input("Article, désignation ou lot")
    if recherche:
        resultats = rechercher_stock(recherche)
        if not resultats.empty:
            st.caption(f"{len(resultats)} résultat(s) — 20 premiers affichés")
            for _, produit in resultats.head(20).iterrows():
                with st.container(border=True):
                    afficher_fiche(produit.to_dict(), cle_suffix="rech")
        else:
            st.warning("Aucun résultat.")