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
    try:
        response = requests.get(url)
        response.raise_for_status()  # Vérifie si la requête HTTP a réussi
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur de connexion : {e}")
        return pd.DataFrame()  # Retourne un DataFrame vide en cas d’erreur

    soup = BeautifulSoup(response.text, "html.parser")

    cotes = soup.find_all("div", class_="cote")
    equipes = soup.find_all("span", class_="nom-equipe")

    data = [{"Équipe": equipe.text, "Cote": float(cote.text)} for equipe, cote in zip(equipes, cotes)]

    return pd.DataFrame(data)

# 🔄 Sauvegarde des cotes en base SQLite
def sauvegarder_dans_db(df):
    if df.empty:
        st.warning("Aucune donnée à enregistrer !")
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

# 📊 Prédiction avec XGBoost
def entrainer_modele():
    conn = sqlite3.connect("cotes_fifa.db")

    # Vérifier si la table contient des données avant d’entraîner le modèle
    df = pd.read_sql_query("SELECT * FROM cotes", conn)
    conn.close()

    if df.empty:
        st.warning("Pas assez de données pour entraîner le modèle !")
        return None

    df["variation_cotes"] = df["cote"].diff().fillna(0)  # Calcul des variations

    X = df[["cote", "variation_cotes"]]
    y = np.random.randint(0, 2, size=len(X))  # TODO: Remplacer par des résultats réels

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = XGBClassifier()
    model.fit(X_train, y_train)

    return model

# 🌍 Interface Streamlit
st.title("📊 Analyse des Cotes FIFA Virtuel")

conn = sqlite3.connect("cotes_fifa.db")
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS cotes (id INTEGER PRIMARY KEY AUTOINCREMENT, equipe TEXT, cote REAL, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.commit()
df_affichage = pd.read_sql_query("SELECT * FROM cotes", conn)
conn.close()

st.dataframe(df_affichage)

if st.button("Actualiser les cotes"):
    df_cotes = scrape_cotes()
    sauvegarder_dans_db(df_cotes)
    st.write("✅ Données mises à jour !")

if st.button("Prédire un match"):
    model = entrainer_modele()
    if model:
        nouvelle_cote = np.array([[1.85, -0.05]])
        prediction = model.predict(nouvelle_cote)
        st.success(f"🔮 Résultat prédit : {'Équipe 1' if prediction[0] == 1 else 'Équipe 2'}")
