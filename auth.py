"""
Authentification simple par nom d'utilisateur / mot de passe, avec rôles.
Les identifiants sont stockés (hashés) dans data/utilisateurs.csv.
"""
import streamlit as st
import pandas as pd
import hashlib
import os

USERS_PATH = "data/utilisateurs.csv"


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def init_default_users():
    """Crée le fichier utilisateurs avec des comptes par défaut s'il n'existe pas."""
    if not os.path.exists(USERS_PATH):
        os.makedirs(os.path.dirname(USERS_PATH), exist_ok=True)
        df = pd.DataFrame([
            {"nom_utilisateur": "admin", "mot_de_passe_hash": hash_password("admin123"), "role": "admin"},
            {"nom_utilisateur": "responsable", "mot_de_passe_hash": hash_password("resp123"), "role": "responsable"},
            {"nom_utilisateur": "magasinier", "mot_de_passe_hash": hash_password("mag123"), "role": "magasinier"},
        ])
        df.to_csv(USERS_PATH, index=False)


def charger_utilisateurs():
    init_default_users()
    return pd.read_csv(USERS_PATH)


def verifier_identifiants(nom_utilisateur, mot_de_passe):
    df = charger_utilisateurs()
    match = df[df["nom_utilisateur"] == nom_utilisateur]
    if match.empty:
        return None
    if match.iloc[0]["mot_de_passe_hash"] == hash_password(mot_de_passe):
        return match.iloc[0]["role"]
    return None


def afficher_login():
    """Affiche le formulaire de connexion si besoin. Retourne True si l'utilisateur est connecté."""
    if st.session_state.get("authentifie"):
        return True

    st.title("🔐 Connexion — Maklada QR Traçabilité")
    with st.form("login_form"):
        nom_utilisateur = st.text_input("Nom d'utilisateur")
        mot_de_passe = st.text_input("Mot de passe", type="password")
        submit = st.form_submit_button("Se connecter")
        if submit:
            role = verifier_identifiants(nom_utilisateur, mot_de_passe)
            if role:
                st.session_state["authentifie"] = True
                st.session_state["utilisateur"] = nom_utilisateur
                st.session_state["role"] = role
                st.rerun()
            else:
                st.error("Nom d'utilisateur ou mot de passe incorrect.")

    st.caption(
        "Comptes par défaut : admin/admin123 · responsable/resp123 · magasinier/mag123 "
        "— à changer dans data/utilisateurs.csv avant mise en production."
    )
    return False


def afficher_deconnexion():
    with st.sidebar:
        st.write(f"👤 Connecté : **{st.session_state.get('utilisateur', '?')}** "
                  f"({st.session_state.get('role', '?')})")
        if st.button("Se déconnecter"):
            for k in ["authentifie", "utilisateur", "role"]:
                st.session_state.pop(k, None)
            st.rerun()


def exige_connexion():
    """À appeler en haut de chaque page. Arrête l'exécution si non connecté."""
    if not afficher_login():
        st.stop()
    afficher_deconnexion()