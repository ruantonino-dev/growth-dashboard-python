import streamlit as st
import pandas as pd
from supabase import create_client

# Configurazione interfaccia
st.set_page_config(page_title="Tony Russo Growth DB", layout="wide", initial_sidebar_state="expanded")

# CSS Custom per rendere la UI più professionale
st.markdown("""
    <style>
    .stMultiSelect div div div div { background-color: #1e293b !important; color: white !important; }
    .stButton>button { width: 100%; background-color: #3b82f6; color: white; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# Collegamento Cloud
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

@st.cache_data(ttl=600) # Cache di 10 minuti per non stressare il database
def get_data():
    res = supabase.table("ideas").select("*").execute()
    return pd.DataFrame(res.data)

# Caricamento dati
df_raw = get_data()

# --- SIDEBAR FILTRI ---
st.sidebar.title("🎯 Filtri Avanzati")

# 1. Ricerca Testuale
search = st.sidebar.text_input("🔍 Cerca parola chiave", "", help="Cerca nell'idea o nei dettagli")

# 2. Filtro Categoria
categories = ["Tutte"] + sorted(df_raw['categoria'].unique().tolist())
cat_filter = st.sidebar.selectbox("📁 Categoria", categories)

# 3. Filtro Stato
stati = ["Tutti", "Fattibile", "Da fare", "In progress", "Fatto"]
stato_filter = st.sidebar.selectbox("🚦 Stato Attuale", stati)

# 4. Filtro Tag (Multi-selezione)
# Pulizia tag: estraiamo tutti i singoli tag presenti nel DB
all_tags = set()
for t_str in df_raw['tag'].dropna():
    tags = [t.strip() for t in t_str.split() if t.startswith('#')]
    all_tags.update(tags)
tag_filter = st.sidebar.multiselect("🏷️ Filtra per Tag", sorted(list(all_tags)))

# --- LOGICA DI FILTRAGGIO ---
df = df_raw.copy()

if cat_filter != "Tutte":
    df = df[df['categoria'] == cat_filter]

if stato_filter != "Tutti":
    df = df[df['stato'] == stato_filter]

if search:
    df = df[df['idea'].str.contains(search, case=False) | df['dettagli'].str.contains(search, case=False)]

if tag_filter:
    # Filtra le righe che contengono ALMENO uno dei tag selezionati
    df = df[df['tag'].apply(lambda x: any(t in x for t in tag_filter))]

# --- UI PRINCIPALE ---
st.title("📊 Growth Master Dashboard")
st.caption(f"Stai visualizzando {len(df)} idee su 1.000 in base ai filtri selezionati.")

# Editor Interattivo
edited_df = st.data_editor(
    df,
    column_config={
        "id": st.column_config.Column("ID", disabled=True),
        "idea": st.column_config.Column("Idea Strategica", width="medium", disabled=True),
        "dettagli": st.column_config.Column("Esecuzione Dettagliata", width="large", disabled=True),
        "stato": st.column_config.SelectboxColumn(
            "Stato", 
            options=["Fattibile", "Da fare", "In progress", "Fatto"],
            required=True
        ),
        "note": st.column_config.TextColumn("Note Strategiche (Editabili)", width="medium"),
        "tag": st.column_config.Column("Tags", disabled=True),
        "categoria": st.column_config.Column("Categoria", disabled=True),
    },
    hide_index=True,
    use_container_width=True,
    key="main_editor"
)

# --- SALVATAGGIO ---
st.sidebar.markdown("---")
if st.sidebar.button("💾 SALVA MODIFICHE"):
    with st.spinner("Sincronizzazione Cloud..."):
        # Troviamo solo le righe modificate per non sovraccaricare il sistema
        for index, row in edited_df.iterrows():
            # Update su Supabase
            supabase.table("ideas").update({
                "stato": row['stato'],
                "note": row['note']
            }).eq("id", row['id']).execute()
            
    st.sidebar.success("Dati sincronizzati!")
    st.cache_data.clear() # Svuota la cache per mostrare i dati aggiornati
    st.rerun()

# Footer informativo
st.sidebar.info("""
**Istruzioni:**
1. Usa i filtri per isolare le strategie.
2. Modifica 'Stato' o 'Note' direttamente in tabella.
3. Clicca su 'Salva' per rendere le modifiche permanenti.
""")
