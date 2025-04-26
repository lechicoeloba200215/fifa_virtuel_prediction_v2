import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
import numpy as np
import streamlit as st

# 🔍 Scraping des cotes FIFA Virtuel
def scrape_cotes():
    url = "https://www.exemple-bookmaker.com/fifa-virtuel"  # À adapter selon le site
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    cotes = soup.find_all("div", class_="cote")
    equipes = soup.find_all("span", class_="nom-equipe")

    data = []
    for equipe, cote in zip(equipes, cotes):
        data.append({"Équipe": equipe.text, "Cote": float(cote.text)})

    return pd.DataFrame(data)

# 🔄 Sauvegarde des cotes en base SQLite
def sauvegarder_dans_db(df):
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

# 📊 Prédiction avec XGBoost
def entrainer_modele():
    conn = sqlite3.connect("cotes_fifa.db")
    df = pd.read_sql_query("SELECT * FROM cotes", conn)
    conn.close()

    df["variation_cotes"] = df["cote"] - df["cote"].shift(1)
    df = df.dropna()

    X = df[["cote", "variation_cotes"]]
    y = np.random.randint(0, 2, size=len(X))  # Simuler des résultats de match

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = XGBClassifier()
    model.fit(X_train, y_train)

    return model

# 🌍 Interface Streamlit
model = entrainer_modele()
conn = sqlite3.connect("cotes_fifa.db")
df_affichage = pd.read_sql_query("SELECT * FROM cotes", conn)
conn.close()

st.title("📊 Analyse des Cotes FIFA Virtuel")
st.dataframe(df_affichage)

if st.button("Actualiser les cotes"):
    df_cotes = scrape_cotes()
    sauvegarder_dans_db(df_cotes)
    st.write("✅ Données mises à jour !")

if st.button("Prédire un match"):
    nouvelle_cote = np.array([[1.85, -0.05]])
    prediction = model.predict(nouvelle_cote)
    st.success(f"🔮 Résultat prédit : {'Équipe 1' if prediction[0] == 1 else 'Équipe 2'}")
