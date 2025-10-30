# app.py
import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
import os
import base64

# ---------- Config ----------
st.set_page_config(page_title="Mostruário Digital - CLAMI", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "logos", "clami-positivo_.jpg")
CSV_PATH = os.path.join(BASE_DIR, "catalogo.csv")

# ---------- Helpers ----------
@st.cache_data(ttl=300)
def load_data(path=CSV_PATH):
    """Carrega o CSV, tenta UTF-8 e Latin-1."""
    try:
        df = pd.read_csv(path, dtype=str, encoding="utf-8").fillna("")
    except UnicodeDecodeError:
        df = pd.read_csv(path, dtype=str, encoding="latin-1").fillna("")
    except Exception as e:
        st.error(f"Erro ao ler {path}: {e}")
        df = pd.DataFrame(columns=[
            "codigo", "faixa", "referencia", "composicao",
            "status", "data_atualizacao", "imagem_url"
        ])
    return df

def status_color(status_text):
    """Define cor conforme o status."""
    s = str(status_text).strip().lower()
    if "fora" in s:
        return "#D9534F"  # vermelho
    if "susp" in s:
        return "#F0AD4E"  # laranja
    if "ativo" in s:
        return "#5CB85C"  # verde
    return "#6c757d"  # cinza

# ---------- Cabeçalho ----------
logo_html = ""
if os.path.exists(LOGO_PATH):
    try:
        with open(LOGO_PATH, "rb") as f:
            logo_bytes = f.read()
        logo_b64 = base64.b64encode(logo_bytes).decode()
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" width="200" style="margin-bottom:5px;">'
    except Exception:
        logo_html = ""
else:
    logo_html = "<div style='font-weight:700; font-size:28px;'>clami</div>"

st.markdown(
    f"""
    <div style="text-align:left; margin-left:0; margin-bottom:10px;">
        {logo_html}
        <h1 style="color:#0b3d91; margin-top:5px; margin-bottom:10px;">MOSTRUÁRIO DIGITAL</h1>
    </div>
    <hr style="border:1px solid #ccc; margin-top:0; margin-bottom:25px;">
    """,
    unsafe_allow_html=True
)

# ---------- Carregar dados ----------
df = load_data(CSV_PATH)
df.columns = [c.strip().lower() for c in df.columns]
expected_cols = ["codigo", "faixa", "referencia", "composicao", "status", "data_atualizacao", "imagem_url"]
for c in expected_cols:
    if c not in df.columns:
        df[c] = ""

# ---------- Filtros ----------
st.sidebar.header("Filtros")

# --- Código (Fornecedor) ---
codigos = ["Todos"] + sorted(df["codigo"].dropna().unique().tolist())
codigo_sel = st.sidebar.selectbox("Código (fornecedor)", codigos)

# --- Faixa (agora dependente do fornecedor) ---
if codigo_sel and codigo_sel != "Todos":
    faixas_filtradas = sorted(df.loc[df["codigo"] == codigo_sel, "faixa"].dropna().unique().tolist())
else:
    faixas_filtradas = sorted([f for f in df["faixa"].dropna().unique().tolist() if f])

faixa_sel = st.sidebar.multiselect("Faixa", options=faixas_filtradas, default=[], placeholder="Selecione as faixas")

# --- Status ---
status_opts = ["Todos"] + sorted(df["status"].dropna().unique().tolist())
status_sel = st.sidebar.selectbox("Status", status_opts)

# --- Última atualização ---
ultima_data = None
try:
    if codigo_sel and codigo_sel != "Todos":
        subset = df[df["codigo"] == codigo_sel].copy()
        subset["data_parsed"] = pd.to_datetime(subset["data_atualizacao"], errors="coerce")
        ultima_data = subset["data_parsed"].max()
    else:
        df_tmp = df.copy()
        df_tmp["data_parsed"] = pd.to_datetime(df_tmp["data_atualizacao"], errors="coerce")
        ultima_data = df_tmp["data_parsed"].max()
except Exception:
    ultima_data = None

if pd.notna(ultima_data):
    st.sidebar.markdown(f"🕓 **Última atualização:** {ultima_data.strftime('%d/%m/%Y')}")
else:
    st.sidebar.markdown("🕓 **Última atualização:** -")

# --- Busca ---
q = st.sidebar.text_input("Busca livre (referência / composição)")

# ---------- Aplicar filtros ----------
filtered = pd.DataFrame()
if (
    (codigo_sel and codigo_sel != "Todos")
    or faixa_sel
    or (status_sel and status_sel != "Todos")
    or (q and q.strip() != "")
):
    filtered = df.copy()

    if codigo_sel and codigo_sel != "Todos":
        filtered = filtered[filtered["codigo"] == codigo_sel]

    if faixa_sel:
        filtered = filtered[filtered["faixa"].isin(faixa_sel)]

    if status_sel and status_sel != "Todos":
        filtered = filtered[filtered["status"] == status_sel]

    if q:
        qlow = q.lower()
        mask = filtered.apply(
            lambda r: qlow in str(r.get("referencia", "")).lower()
            or qlow in str(r.get("composicao", "")).lower(),
            axis=1,
        )
        filtered = filtered[mask]

# ---------- Exibição ----------
if filtered.empty:
    if (
        (codigo_sel and codigo_sel != "Todos")
        or faixa_sel
        or (status_sel and status_sel != "Todos")
        or (q and q.strip() != "")
    ):
        st.info("Nenhum registro encontrado com os filtros selecionados.")
    else:
        st.info("Use os filtros ao lado para visualizar os produtos do mostruário.")
else:
    grouped = filtered.sort_values(["faixa", "referencia"]).groupby("faixa", sort=False)
    first = True
    for faixa, group in grouped:
        # linha divisória (exceto antes da primeira faixa)
        if not first:
            st.markdown("<hr style='border:1px solid #ccc; margin:40px 0;'>", unsafe_allow_html=True)
        first = False

        # título da faixa (sem a palavra "Faixa")
        st.markdown(f"<h3 style='margin-top:10px; color:#0b3d91;'>{faixa}</h3>", unsafe_allow_html=True)

        imgs_per_row = 5
        cols = st.columns(imgs_per_row)
        i = 0
        for _, row in group.iterrows():
            col = cols[i % imgs_per_row]
            with col:
                img_url = row.get("imagem_url", "")
                if img_url:

# Caminho da imagem hospedada no GitHub
img_github = f"https://raw.githubusercontent.com/mostruario/mostruario-digital-clami/main/{img_url}"

try:
    st.image(img_github, use_container_width=True)
except Exception:
    ref = str(row.get("referencia", "")).replace(" ", "+")
    st.image(f"https://placehold.co/400x300?text={ref}", use_container_width=True)

                # Legendas
                st.markdown(f"**{row.get('referencia', '')}**")
                st.markdown(f"{row.get('composicao', '')}")
                color = status_color(row.get('status', ''))
                st.markdown(
                    f"""
                    <div style='
                        color:{color};
                        font-weight:800;
                        font-size:20px;
                        text-align:left;
                        margin-top:6px;
                    '>
                        {row.get('status', '')}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            i += 1
            if i % imgs_per_row == 0 and i < len(group):
                cols = st.columns(imgs_per_row)

# ---------- Rodapé ----------
st.markdown("---")
st.caption("Catálogo gerado localmente — Clami. Atualize o arquivo catalogo.csv para alterar o conteúdo.")

