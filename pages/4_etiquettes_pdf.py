import streamlit as st
import pandas as pd
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from auth import exige_connexion
from labels import generer_etiquette

st.set_page_config(page_title="Planche PDF", page_icon="🖨️", layout="centered")
exige_connexion()

DATA_PATH = "data/stock_maklada.csv"

@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH)

df = load_data()

st.title("🖨️ Planche d'étiquettes PDF")
st.write("Génère un PDF prêt à imprimer avec plusieurs étiquettes par page (format A4).")

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

if len(lignes) > 200:
    st.warning("Plus de 200 lignes — le PDF sera volumineux et long à générer.")

if not lignes.empty and st.button(f"🖨️ Générer le PDF ({len(lignes)} étiquette(s))"):
    with st.spinner("Génération du PDF en cours..."):
        buf_pdf = io.BytesIO()
        c = canvas.Canvas(buf_pdf, pagesize=A4)
        page_w, page_h = A4

        # 2 colonnes x 5 lignes = 10 étiquettes par page A4
        marge = 10 * mm
        cols, rows = 2, 5
        etiquette_w = (page_w - 2 * marge) / cols
        etiquette_h = (page_h - 2 * marge) / rows

        for idx, (_, produit) in enumerate(lignes.iterrows()):
            pos_sur_page = idx % (cols * rows)
            if pos_sur_page == 0 and idx != 0:
                c.showPage()

            col = pos_sur_page % cols
            row = pos_sur_page // cols

            x = marge + col * etiquette_w
            y = page_h - marge - (row + 1) * etiquette_h

            img = generer_etiquette(produit, label_w=520, label_h=260)
            img_buf = io.BytesIO()
            img.save(img_buf, format="PNG")
            img_buf.seek(0)

            from reportlab.lib.utils import ImageReader
            img_reader = ImageReader(img_buf)

            # Redimensionner en conservant le ratio dans la cellule
            marge_interne = 3 * mm
            cell_w = etiquette_w - 2 * marge_interne
            cell_h = etiquette_h - 2 * marge_interne
            ratio = min(cell_w / 520, cell_h / 260)
            draw_w, draw_h = 520 * ratio, 260 * ratio

            c.rect(x, y, etiquette_w, etiquette_h)  # contour pour découpe
            c.drawImage(
                img_reader,
                x + (etiquette_w - draw_w) / 2,
                y + (etiquette_h - draw_h) / 2,
                width=draw_w, height=draw_h
            )

        c.save()
        buf_pdf.seek(0)

        st.success(f"PDF généré : {len(lignes)} étiquette(s) sur "
                   f"{-(-len(lignes) // (cols * rows))} page(s).")
        st.download_button(
            "⬇️ Télécharger le PDF",
            data=buf_pdf.getvalue(),
            file_name="planche_etiquettes_maklada.pdf",
            mime="application/pdf"
        )