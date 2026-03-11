import streamlit as st
import pandas as pd
from supabase import create_client

# Configurazione interfaccia
st.set_page_config(page_title="Tony Russo Growth DB", layout="wide")

# Collegamento Cloud (credenziali sicure)
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.title("📊 Tony Russo | Growth Master Dashboard")

# Funzione per leggere i dati
def get_data():
    res = supabase.table("ideas").select("*").execute()
    return pd.DataFrame(res.data)

data = get_data()

# Filtri veloci in alto
col1, col2 = st.columns([2, 1])
with col1:
    search = st.text_input("🔍 Cerca nell'idea o nei dettagli", "")
with col2:
    cat_filter = st.selectbox("📁 Filtra per Categoria", ["Tutte"] + list(data['categoria'].unique()))

# Logica di filtraggio
filtered = data.copy()
if cat_filter != "Tutte":
    filtered = filtered[filtered['categoria'] == cat_filter]
if search:
    filtered = filtered[filtered['idea'].str.contains(search, case=False) | filtered['dettagli'].str.contains(search, case=False)]

# L'Editor Interattivo
st.subheader("Naviga, Modifica Stato e Aggiungi Note")
st.info("Puoi modificare i campi 'Stato' e 'Note' direttamente nella tabella qui sotto.")

edited_df = st.data_editor(
    filtered,
    column_config={
        "id": "ID",
        "idea": st.column_config.Column("Idea Strategica", width="medium", disabled=True),
        "dettagli": st.column_config.Column("Esecuzione", width="large", disabled=True),
        "stato": st.column_config.SelectboxColumn("Stato", options=["Fattibile", "Da fare", "In progress", "Fatto"]),
        "note": st.column_config.TextColumn("Note Personali", width="medium"),
        "tag": st.column_config.Column("Tags", disabled=True),
        "categoria": st.column_config.Column("Categoria", disabled=True),
    },
    hide_index=True,
    use_container_width=True
)

# Tasto di salvataggio
if st.button("🚀 Sincronizza modifiche su tutti i dispositivi"):
    with st.spinner("Salvataggio in corso..."):
        for index, row in edited_df.iterrows():
            # Aggiorna solo se modificato (semplificato per velocità)
            supabase.table("ideas").update({
                "stato": row['stato'],
                "note": row['note']
            }).eq("id", row['id']).execute()
    st.success("Dati salvati nel Cloud con successo!")
    st.balloons()
