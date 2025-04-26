import pandas as pd
import sqlite3
import numpy as np
import streamlit as st
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager  

# 🔍 Chargement du fichier CSV avec encodage UTF-8
def charger_historique():
    try:
        chemin_fichier = "https://raw.githubusercontent.com/lechicoeloba200215/prédiction-virtuelle-fifa-v2/main/donnee_dFIFA_3x3.csv"

        df = pd.read_csv(chemin_fichier, encoding="utf-8")  # ✅ Correction encodage

        colonnes_attendues = ["v1", "X", "v2", "Résultat", "1Mi-Temps", "2 Mi-Temps"]
        if not all(col in df.columns for col in colonnes_attendues):
            st.error("❌ Erreur : Le fichier CSV ne contient pas toutes les colonnes nécessaires !")
            return pd.DataFrame()

        st.write("✅ Fichier CSV chargé avec succès !")
        return df  

    except Exception as e:
        st.error(f"🚨 Erreur de lecture du fichier CSV : {e}")
        return pd.DataFrame()

# 🔄 Sauvegarde des cotes en base SQLite
def sauvegarder_dans_db():
    df = charger_historique()

    if df.empty:
        st.warning("❌ Aucune donnée à enregistrer ! Vérifie le fichier CSV.")
        return

    try:
        conn = sqlite3.connect("cotes_fifa.db")
        cursor = conn.cursor()

        # Créer la table si elle n'existe pas
        cursor.execute('''CREATE TABLE IF NOT EXISTS cotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            v1 REAL,
            X REAL,
            v2 REAL,
            resultat INTEGER,
            mi_temps_1 INTEGER,
            mi_temps_2 INTEGER,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        # Ajouter les nouvelles données
        for _, row in df.iterrows():
            cursor.execute("INSERT INTO cotes (v1, X, v2, resultat, mi_temps_1, mi_temps_2) VALUES (?, ?, ?, ?, ?, ?)", 
                           (row["v1"], row["X"], row["v2"], row["Resultat"], row["1Mi-Temps"], row["2 Mi-Temps"]))

        conn.commit()
        conn.close()

        st.success("✅ Données enregistrées avec succès !")

    except Exception as e:
        st.error(f"🚨 Erreur lors de l’enregistrement des données : {e}")

# 📊 Prédiction avec XGBoost
def entrainer_modele():
    df = charger_historique()
    
    if df.empty:
        st.warning("⚠️ Pas assez de données pour entraîner le modèle !")
        return None

    X = df[["v1", "X", "v2"]]
    y = df["Resultat"]  

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = XGBClassifier()
    model.fit(X_train, y_train)

    return model

# 🌍 Interface Streamlit
st.title("📊 Analyse des Cotes FIFA Virtuel")

if st.button("Actualiser les cotes"):
    sauvegarder_dans_db()

if st.button("Prédire un match"):
    model = entrainer_modele()
    if model:
        nouvelle_cote = np.array([[1.85, 3.10, 2.00]])  
        prediction = model.predict(nouvelle_cote)
        st.success(f"🔮 Résultat prédit : {prediction[0]}")
