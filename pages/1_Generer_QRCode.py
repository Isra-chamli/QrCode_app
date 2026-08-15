import streamlit as st
import qrcode
from PIL import Image, ImageDraw, ImageFont
import io
from db import charger_stock, rechercher_stock

st.set_page_config(page_title="Générer QR Code", page_icon="🏷️", layout="centered")

st.title("🏷️ Générer une étiquette QR Code")

st.write("Recherche une ligne de stock (article, désignation ou lot) pour générer son étiquette.")
recherche = st.text_input("Rechercher", placeholder="ex: AAB-BC, ACIER, OF26-0101")

resultats = rechercher_stock(recherche) if recherche else charger_stock().head(50)

if resultats.empty:
    st.warning("Aucun résultat.")
    st.stop()

def format_choix(i):
    ligne = resultats.loc[resultats["id"] == i].iloc[0]
    return f"{ligne['article']} | Lot {ligne['lot']} | Emp. {ligne['emplacement']} | {ligne['entrepot']}"

choix = st.selectbox("Choisir la ligne de stock", resultats["id"], format_func=format_choix)

produit = resultats[resultats["id"] == choix].iloc[0]

def val(x, default="-"):
    return default if x is None or (isinstance(x, float) and x != x) else x

# Contenu encodé dans le QR : identifiant unique de la ligne de stock
qr_content = f"MAKLADA-ID:{produit['id']}"

qr = qrcode.QRCode(box_size=8, border=2)
qr.add_data(qr_content)
qr.make(fit=True)
qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

# Construction de l'étiquette imprimable (QR + infos texte)
label_w, label_h = 520, 260
label = Image.new("RGB", (label_w, label_h), "white")
qr_resized = qr_img.resize((220, 220))
label.paste(qr_resized, (10, 20))

draw = ImageDraw.Draw(label)
try:
    font_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 17)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
except Exception:
    font_bold = ImageFont.load_default()
    font = ImageFont.load_default()

x_text = 250
article_num = produit["article"]
designation = str(val(produit["designation"]))[:32]
lot = val(produit["lot"])
emplacement = val(produit["emplacement"])
entrepot = val(produit["entrepot"])
site = val(produit["site"])
stock = val(produit["stock_physique"])
stock_str = f"{stock:,.0f}".replace(",", " ") if not isinstance(stock, str) else stock
ligne_id = produit["id"]

draw.text((x_text, 20), str(article_num), font=font_bold, fill="black")
draw.text((x_text, 48), designation, font=font, fill="black")
draw.text((x_text, 75), f"Lot: {lot}", font=font, fill="black")
draw.text((x_text, 98), f"Emplacement: {emplacement}", font=font, fill="black")
draw.text((x_text, 121), f"Entrepôt: {entrepot}", font=font, fill="black")
draw.text((x_text, 144), f"Site: {site}", font=font, fill="black")
draw.text((x_text, 167), f"Stock physique: {stock_str}", font=font, fill="black")
draw.text((x_text, 190), f"ID ligne: {ligne_id}", font=font, fill="black")

st.image(label, caption="Aperçu de l'étiquette", use_container_width=False)

buf = io.BytesIO()
label.save(buf, format="PNG")
nom_fichier = f"etiquette_{article_num}_{val(lot, 'lot')}.png"
st.download_button(
    "⬇️ Télécharger l'étiquette (PNG)",
    data=buf.getvalue(),
    file_name=nom_fichier,
    mime="image/png"
)

with st.expander("Détails complets de la ligne"):
    st.json(produit.to_dict())