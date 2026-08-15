"""
Module partagé d'accès à la base de données Maklada (SQLite).
Toutes les pages importent ce module au lieu de lire directement le CSV.
"""
import sqlite3
import pandas as pd
from datetime import datetime
import streamlit as st

DB_PATH = "data/maklada.db"


def get_connection():
    """Connexion SQLite avec accès par nom de colonne."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@st.cache_data(ttl=30)
def charger_stock():
    """Charge toute la table stock en DataFrame (rafraîchi toutes les 30s)."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM stock", conn)
    conn.close()
    return df


def get_ligne(ligne_id):
    """Récupère une ligne de stock par son id."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM stock WHERE id = ?", (ligne_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def rechercher_stock(terme):
    """Recherche dans article, designation, lot."""
    conn = get_connection()
    like = f"%{terme}%"
    df = pd.read_sql_query(
        """
        SELECT * FROM stock
        WHERE article LIKE ? OR designation LIKE ? OR lot LIKE ?
        LIMIT 200
        """,
        conn,
        params=(like, like, like),
    )
    conn.close()
    return df


def enregistrer_mouvement(ligne_id, type_mouvement, quantite, utilisateur="inconnu"):
    """
    Enregistre une entrée ou sortie de stock et met à jour le stock physique.
    type_mouvement: 'entree' ou 'sortie'
    """
    conn = get_connection()
    cur = conn.cursor()

    # Enregistrer le mouvement
    cur.execute(
        """INSERT INTO mouvements (ligne_id, type_mouvement, quantite, utilisateur, date_mouvement)
           VALUES (?, ?, ?, ?, ?)""",
        (ligne_id, type_mouvement, quantite, utilisateur, datetime.now().isoformat()),
    )

    # Mettre à jour le stock physique
    delta = quantite if type_mouvement == "entree" else -quantite
    cur.execute(
        "UPDATE stock SET stock_physique = stock_physique + ?, physique_disponible = physique_disponible + ? WHERE id = ?",
        (delta, delta, ligne_id),
    )

    conn.commit()
    conn.close()
    charger_stock.clear()  # invalider le cache pour refléter le nouveau stock


def enregistrer_scan(ligne_id, utilisateur="inconnu", action="consultation"):
    """Journalise un scan pour la traçabilité."""
    conn = get_connection()
    conn.execute(
        """INSERT INTO scans_historique (ligne_id, utilisateur, action, date_scan)
           VALUES (?, ?, ?, ?)""",
        (ligne_id, utilisateur, action, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def historique_ligne(ligne_id):
    """Retourne mouvements + scans pour une ligne donnée, triés par date."""
    conn = get_connection()
    mouvements = pd.read_sql_query(
        "SELECT * FROM mouvements WHERE ligne_id = ? ORDER BY date_mouvement DESC",
        conn, params=(ligne_id,)
    )
    scans = pd.read_sql_query(
        "SELECT * FROM scans_historique WHERE ligne_id = ? ORDER BY date_scan DESC",
        conn, params=(ligne_id,)
    )
    conn.close()
    return mouvements, scans