import streamlit as st
import pandas as pd
from supabase import create_client

# Configurazione interfaccia
st.set_page_config(page_title="Tony Russo Growth DB", layout="wide", initial_sidebar_state="expanded")

# CSS Custom per stile professionale e colori semaforici nelle selectbox
st.markdown("""
    <style>
    .stMultiSelect div div div div { background-color: #1e293b !important; color: white !important; }
    .stButton>button { width: 100%; background-color: #3b82f6; color: white; border-radius: 8px; border: none; padding: 10px; font-weight: bold; }
    .stButton>button:hover { background-color: #2563eb; }
    /* Estetica generale */
    .stApp { background-color: #0f172a; color: white; }
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
st.sidebar.title("🎯 Strategia & Filtri")

search = st.sidebar.text_input("🔍 Cerca parola chiave", "")

categories = ["Tutte"] + sorted(df_raw['categoria'].unique().tolist())
cat_filter = st.sidebar.selectbox("📁 Categoria", categories)

stati_disponibili = ["Attivi (Escl. Cestinati)", "Da valutare", "Fattibile", "Da fare", "In progress", "Fatto", "Cestinato", "Tutti"]
stato_filter = st.sidebar.selectbox("🚦 Stato Strategia", stati_disponibili)

all_tags = set()
for t_str in df_raw['tag'].dropna():
    tags = [t.strip() for t in t_str.split() if t.startswith('#')]
    all_tags.update(tags)
tag_filter = st.sidebar.multiselect("🏷️ Filtra per Tag", sorted(list(all_tags)))

# --- LOGICA DI FILTRAGGIO ---
df = df_raw.copy()

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

# Configurazione colori semaforici per lo stato
# Streamlit permette di associare icone/colori tramite SelectboxColumn
edited_df = st.data_editor(
    df,
    column_config={
        "id": st.column_config.Column("ID", disabled=True),
        "idea": st.column_config.Column("Idea Strategica", width="medium", disabled=True),
        "dettagli": st.column_config.Column("Esecuzione", width="large", disabled=True),
        "stato": st.column_config.SelectboxColumn(
            "Stato", 
            help="Cambia lo stato della strategia",
            options=[
                "Da valutare",
                "Fattibile",
                "Da fare",
                "In progress",
                "Fatto",
                "Cestinato"
            ],
            required=True,
        ),
        "note": st.column_config.TextColumn("Note Strategiche", width="medium"),
        "tag": st.column_config.Column("Tags", disabled=True),
        "categoria": st.column_config.Column("Categoria", disabled=True),
    },
    hide_index=True,
    use_container_width=True,
    key="main_editor"
)

# --- LOGICA COLORE (Visuale solo in output se necessario, ma il data_editor usa le selectbox) ---
# Per un tocco in più, mostriamo un riepilogo semaforico in sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("📈 Riepilogo Status")
counts = df_raw['stato'].value_counts()
st.sidebar.write(f"🟢 Fatto: {counts.get('Fatto', 0)}")
st.sidebar.write(f"🟡 In progress: {counts.get('In progress', 0)}")
st.sidebar.write(f"🟠 Da fare: {counts.get('Da fare', 0)}")
st.sidebar.write(f"🔵 Fattibile: {counts.get('Fattibile', 0)}")
st.sidebar.write(f"⚪ Da valutare: {counts.get('Da valutare', 0)}")
st.sidebar.write(f"🔴 Cestinato: {counts.get('Cestinato', 0)}")

# --- SALVATAGGIO ---
st.sidebar.markdown("---")
if st.sidebar.button("💾 SALVA E SINCRONIZZA"):
    with st.spinner("Sincronizzazione Cloud in corso..."):
        for index, row in edited_df.iterrows():
            supabase.table("ideas").update({
                "stato": row['stato'],
                "note": row['note']
            }).eq("id", row['id']).execute()
            
    st.sidebar.success("Dati aggiornati!")
    st.cache_data.clear()
    st.rerun()
