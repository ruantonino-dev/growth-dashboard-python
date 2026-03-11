import streamlit as st
import pandas as pd
from supabase import create_client

# Configurazione interfaccia
st.set_page_config(page_title="Tony Russo Growth DB", layout="wide", initial_sidebar_state="expanded")

# CSS Custom per stile professionale
st.markdown("""
    <style>
    .stMultiSelect div div div div { background-color: #1e293b !important; color: white !important; }
    .stButton>button { width: 100%; background-color: #3b82f6; color: white; border-radius: 8px; border: none; padding: 10px; }
    .stButton>button:hover { background-color: #2563eb; }
    </style>
    """, unsafe_allow_html=True)

# Collegamento Cloud
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

@st.cache_data(ttl=300)
def get_data():
    res = supabase.table("ideas").select("*").execute()
    return pd.DataFrame(res.data)

df_raw = get_data()

# --- SIDEBAR FILTRI ---
st.sidebar.title("🎯 Filtri Avanzati")

# 1. Ricerca Testuale
search = st.sidebar.text_input("🔍 Cerca parola chiave", "")

# 2. Filtro Categoria
categories = ["Tutte"] + sorted(df_raw['categoria'].unique().tolist())
cat_filter = st.sidebar.selectbox("📁 Categoria", categories)

# 3. Filtro Stato (Aggiornato con 'Cestinato' e 'Da valutare')
# Di base escludiamo i cestinati per tenere pulita la vista
stati_disponibili = ["Attivi (Escl. Cestinati)", "Da valutare", "Fattibile", "Da fare", "In progress", "Fatto", "Cestinato", "Tutti"]
stato_filter = st.sidebar.selectbox("🚦 Stato Strategia", stati_disponibili)

# 4. Filtro Tag
all_tags = set()
for t_str in df_raw['tag'].dropna():
    tags = [t.strip() for t in t_str.split() if t.startswith('#')]
    all_tags.update(tags)
tag_filter = st.sidebar.multiselect("🏷️ Filtra per Tag", sorted(list(all_tags)))

# --- LOGICA DI FILTRAGGIO ---
df = df_raw.copy()

# Gestione filtri stato
if stato_filter == "Attivi (Escl. Cestinati)":
    df = df[df['stato'] != "Cestinato"]
elif stato_filter == "Tutti":
    pass
else:
    df = df[df['stato'] == stato_filter]

if cat_filter != "Tutte":
    df = df[df['categoria'] == cat_filter]

if search:
    df = df[df['idea'].str.contains(search, case=False) | df['dettagli'].str.contains(search, case=False)]

if tag_filter:
    df = df[df['tag'].apply(lambda x: any(t in x for t in tag_filter))]

# --- UI PRINCIPALE ---
st.title("📊 Growth Master Dashboard")
st.caption(f"Stai visualizzando {len(df)} idee strategiche.")

# Definizione stati per la tendina della tabella
lista_stati_tabella = ["Da valutare", "Fattibile", "Da fare", "In progress", "Fatto", "Cestinato"]

edited_df = st.data_editor(
    df,
    column_config={
        "id": st.column_config.Column("ID", disabled=True),
        "idea": st.column_config.Column("Idea Strategica", width="medium", disabled=True),
        "dettagli": st.column_config.Column("Esecuzione", width="large", disabled=True),
        "stato": st.column_config.SelectboxColumn(
            "Stato", 
            options=lista_stati_tabella,
            required=True
        ),
        "note": st.column_config.TextColumn("Note Strategiche", width="medium"),
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
    with st.spinner("Sincronizzazione Cloud in corso..."):
        # Troviamo le differenze rispetto al dataframe originale per aggiornare solo il necessario
        for index, row in edited_df.iterrows():
            supabase.table("ideas").update({
                "stato": row['stato'],
                "note": row['note']
            }).eq("id", row['id']).execute()
            
    st.sidebar.success("Dati sincronizzati!")
    st.cache_data.clear()
    st.rerun()

st.sidebar.info("Tip: Le idee 'Cestinate' vengono nascoste automaticamente per aiutarti a focusare sulle strategie attive.")
