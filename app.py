# app.py
import streamlit as st
import pandas as pd
import os
import base64

# ---------- CONFIGURAÇÕES ----------
st.set_page_config(page_title="Mostruário Digital - CLAMI", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "catalogo.csv")
LOGO_PATH = os.path.join(BASE_DIR, "logos", "clami-positivo_.jpg")

# ---------- FUNÇÕES ----------
@st.cache_data(ttl=300)
def load_data(path=CSV_PATH):
    try:
        df = pd.read_csv(path, dtype=str, encoding="utf-8").fillna("")
    except UnicodeDecodeError:
        df = pd.read_csv(path, dtype=str, encoding="latin-1").fillna("")
    return df

def status_color(status_text):
    s = str(status_text).strip().lower()
    if "fora" in s:
        return "#D9534F"
    elif "susp" in s:
        return "#F0AD4E"
    elif "ativo" in s:
        return "#5CB85C"
    return "#6c757d"

# ---------- CABEÇALHO ----------
logo_html = ""
if os.path.exists(LOGO_PATH):
    with open(LOGO_PATH, "rb") as f:
        logo_bytes = f.read()
    logo_b64 = base64.b64encode(logo_bytes).decode()
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" width="200">'
else:
    logo_html = "<div style='font-weight:700; font-size:28px;'>clami</div>"

st.markdown(
    f"""
    <div style="text-align:left;">
        {logo_html}
        <h1 style="color:#0b3d91;">MOSTRUÁRIO DIGITAL</h1>
    </div>
    <hr style="border:1px solid #ccc; margin-bottom:25px;">
    """,
    unsafe_allow_html=True,
)

# ---------- DADOS ----------
df = load_data()
df.columns = [c.strip().lower() for c in df.columns]

expected_cols = ["codigo", "faixa", "referencia", "composicao", "status", "data_atualizacao", "imagem_url"]
for col in expected_cols:
    if col not in df.columns:
        df[col] = ""

# ---------- SIDEBAR ----------
st.sidebar.header("Filtros")

codigos = ["Todos"] + sorted(df["codigo"].dropna().unique().tolist())
codigo_sel = st.sidebar.selectbox("Código (fornecedor)", codigos)

if codigo_sel != "Todos":
    faixas_filtradas = sorted(df.loc[df["codigo"] == codigo_sel, "faixa"].dropna().unique().tolist())
else:
    faixas_filtradas = sorted(df["faixa"].dropna().unique().tolist())

faixa_sel = st.sidebar.multiselect("Faixa", faixas_filtradas)
status_opts = ["Todos"] + sorted(df["status"].dropna().unique().tolist())
status_sel = st.sidebar.selectbox("Status", status_opts)
busca = st.sidebar.text_input("Busca livre (referência / composição)")

# ---------- FILTROS ----------
filtered = df.copy()

if codigo_sel != "Todos":
    filtered = filtered[filtered["codigo"] == codigo_sel]
if faixa_sel:
    filtered = filtered[filtered["faixa"].isin(faixa_sel)]
if status_sel != "Todos":
    filtered = filtered[filtered["status"] == status_sel]
if busca:
    busca_low = busca.lower()
    filtered = filtered[
        filtered.apply(
            lambda r: busca_low in str(r["referencia"]).lower()
            or busca_low in str(r["composicao"]).lower(),
            axis=1,
        )
    ]

# ---------- EXIBIÇÃO ----------
if filtered.empty:
    st.info("Nenhum resultado encontrado com os filtros aplicados.")
else:
    grouped = filtered.sort_values(["faixa", "referencia"]).groupby("faixa", sort=False)

    for faixa, group in grouped:
        st.markdown(f"<h3 style='color:#0b3d91;'>{faixa}</h3>", unsafe_allow_html=True)
        cols = st.columns(5)
        i = 0
        for _, row in group.iterrows():
            col = cols[i % 5]
            with col:
                img_url = str(row.get("imagem_url", "")).strip()
                ref = str(row.get("referencia", "")).strip()

                # 1️⃣ Caminho local
                local_path = os.path.join(BASE_DIR, img_url.replace("/", os.sep))

                # 2️⃣ Caminho online (GitHub)
                github_url = (
                    f"https://raw.githubusercontent.com/mostruario/mostruario-digital-clami/main/{img_url}"
                )

                # 3️⃣ Exibição
                if os.path.exists(local_path):
                    st.image(local_path, use_container_width=True)
                else:
                    st.image(github_url, use_container_width=True)

                # Texto
                st.markdown(f"**{ref}**")
                st.markdown(f"{row.get('composicao', '')}")
                color = status_color(row.get("status", ""))
                st.markdown(
                    f"<div style='color:{color}; font-weight:800; font-size:20px;'>{row.get('status', '')}</div>",
                    unsafe_allow_html=True,
                )
            i += 1
            if i % 5 == 0:
                cols = st.columns(5)

st.markdown("---")
st.caption("Catálogo CLAMI — atualizado automaticamente via GitHub.")
