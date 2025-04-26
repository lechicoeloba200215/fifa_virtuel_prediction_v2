from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import pandas as pd
import sqlite3
import numpy as np
import streamlit as st

# 🔍 Scraping des cotes FIFA Virtuel avec Selenium
def scrape_cotes():
    url = "https://1xbet.com/fr/new-cyber/virtual/disciplines/fifa/champs/2665392-fc-24-3x3-international-masters-league"

    # Configurer Selenium avec ChromeDriver
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Mode sans interface graphique
    service = Service("chemin_vers_chromedriver")  # Remplace par le chemin réel

    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(url)

    try:
        # Trouver les éléments contenant les cotes et équipes (AJUSTER LES CLASSES CSS)
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
        equipe TEXT,
        cote REAL,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    for _, row in df.iterrows():
        cursor.execute("INSERT INTO cotes (equipe, cote) VALUES (?, ?)", (row["Équipe"], row["Cote"]))

    conn.commit()
    conn.close()

# 🌍 Interface Streamlit
st.title("📊 Analyse des Cotes FIFA Virtuel")

if st.button("Actualiser les cotes"):
    df_cotes = scrape_cotes()
    sauvegarder_dans_db(df_cotes)
    st.write("✅ Données mises à jour !")
