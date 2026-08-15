"""
Module partagé de génération d'étiquettes QR Code.
Utilisé par les pages 1 (génération unitaire), 3 (génération en masse) et 4 (PDF planche).
"""
import qrcode
from PIL import Image, ImageDraw, ImageFont
import pandas as pd


def val(x, default="-"):
    return default if pd.isna(x) else x


def contenu_qr(ligne_id):
    return f"MAKLADA-ID:{ligne_id}"


def generer_etiquette(produit, label_w=520, label_h=260):
    """
    Construit une étiquette imprimable (QR + infos texte) pour une ligne de stock.
    produit : Series ou dict avec les colonnes du CSV stock_maklada.csv
    Retourne une image PIL.
    """
    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(contenu_qr(produit["id"]))
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

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
    article_num = produit["Numéro d'article"]
    designation = str(val(produit["Nom du produit"]))[:32]
    lot = val(produit["Numéro du lot"])
    emplacement = val(produit["Emplacement"])
    entrepot = val(produit["Entrepôt"])
    site = val(produit["Site"])
    stock = val(produit["Stock physique"])
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

    return label


def nom_fichier_etiquette(produit):
    article = produit["Numéro d'article"]
    lot = val(produit["Numéro du lot"], "lot")
    return f"etiquette_{article}_{lot}.png".replace("/", "-").replace(" ", "_")