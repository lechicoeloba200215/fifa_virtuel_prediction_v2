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

# 🔍 Détection automatique du fichier CSV
def charger_historique():
    chemins_possibles = [
        "/storage/emulated/0/files/donnee_dFIFA_3x3.csv",  # Stockage local Android
        "donnee_dFIFA_3x3.csv",  # Fichier local dans le même dossier que le script
        "https://raw.githubusercontent.com/ton-repo/donnee_dFIFA_3x3.csv"  # URL GitHub
    ]

    for chemin_fichier in chemins_possibles:
        try:
            df = pd.read_csv(chemin_fichier)
            
            # Vérifier que les colonnes attendues sont bien présentes
            colonnes_attendues = ["v1", "X", "v2", "Résultat", "1 Mi-Temps", "2 Mi-Temps"]
            if not all(col in df.columns for col in colonnes_attendues):
                st.error("❌ Erreur : Le fichier CSV ne contient pas toutes les colonnes nécessaires !")
                return pd.DataFrame()

            return df  # Fichier chargé avec succès
        
        except Exception:
            continue  # Essaye le prochain chemin si échec
    
    st.error("🚨 Erreur : Fichier CSV introuvable dans tous les chemins testés !")
    return pd.DataFrame()

# 🔍 Scraping des cotes FIFA Virtuel avec Selenium
def scrape_cotes():
    url = "https://1xbet.com/fr/new-cyber/virtual/disciplines/fifa/champs/2665392-fc-24-3x3-international-masters-league"

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver.get(url)

    try:
        equipes = driver.find_elements(By.CLASS_NAME, "nom-equipe-class")
        cotes = driver.find_elements(By.CLASS_NAME, "cote-class")

        if not equipes or not cotes:
            st.warning("⚠️ Impossible de récupérer les cotes, vérifie la structure HTML du site.")
            return pd.DataFrame()

        data = [{"Équipe": equipe.text, "Cote": float(cote.text)} for equipe, cote in zip(equipes, cotes)]

    except Exception as e:
        st.error(f"🚨 Erreur lors du scraping : {e}")
        return pd.DataFrame()

    finally:
        driver.quit()

    return pd.DataFrame(data)

# 🔄 Sauvegarde des cotes en base SQLite
def sauvegarder_dans_db(df):
    if df.empty:
        st.warning("❌ Aucune donnée à enregistrer !")
        return

    conn = sqlite3.connect("cotes_fifa.db")
    cursor = conn.cursor()

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

    for _, row in df.iterrows():
        cursor.execute("INSERT INTO cotes (v1, X, v2, resultat, mi_temps_1, mi_temps_2) VALUES (?, ?, ?, ?, ?, ?)", 
                       (row["v1"], row["X"], row["v2"], row["Résultat"], row["1 Mi-Temps"], row["2 Mi-Temps"]))

    conn.commit()
    conn.close()

# 📊 Prédiction avec XGBoost
def entrainer_modele():
    df = charger_historique()
    
    if df.empty:
        st.warning("⚠️ Pas assez de données pour entraîner le modèle !")
        return None

    X = df[["v1", "X", "v2"]]
    y = df["Résultat"]  # Prédiction du résultat final

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = XGBClassifier()
    model.fit(X_train, y_train)

    return model

# 🌍 Interface Streamlit
st.title("📊 Analyse des Cotes FIFA Virtuel")

if st.button("Actualiser les cotes"):
    df_cotes = charger_historique()
    sauvegarder_dans_db(df_cotes)
    st.write("✅ Données mises à jour !")

if st.button("Prédire un match"):
    model = entrainer_modele()
    if model:
        nouvelle_cote = np.array([[1.85, 3.10, 2.00]])  # Exemple de nouvelles cotes
        prediction = model.predict(nouvelle_cote)
        st.success(f"🔮 Résultat prédit : {prediction[0]}")
