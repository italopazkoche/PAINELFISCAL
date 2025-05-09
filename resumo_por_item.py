import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
import os
import json

# ---------------------------
# CONFIGURAÇÃO
# ---------------------------

# ---------------------------
# CREDENCIAIS (via Streamlit Secrets)
# ---------------------------
credentials = service_account.Credentials.from_service_account_info(info)
client = bigquery.Client(credentials=credentials, project=info["project_id"])

# ---------------------------
# CONSULTA A VIEW RESUMIDA
# ---------------------------
@st.cache_data(ttl=600)
def carregar_resumo_por_item():
    query = "SELECT * FROM `bdxml-459201.nfce_data.v_resumo_por_item_2025`"
    return client.query(query).to_dataframe()

# ---------------------------
# INTERFACE
# ---------------------------
st.title("📈 Resumo de XMLs de Saída por Mês")

df = carregar_resumo_por_item()
df["cliente"] = df["razao_social_emitente"] + " - " + df["cnpj_emitente"]

# Mapeamento de mês -> nome
mapa_meses = {
    1: "Jan/25", 2: "Fev/25", 3: "Mar/25", 4: "Abr/25",
    5: "Mai/25", 6: "Jun/25", 7: "Jul/25", 8: "Ago/25",
    9: "Set/25", 10: "Out/25", 11: "Nov/25", 12: "Dez/25"
}

meses_disponiveis = sorted(df["mes"].unique())
opcoes_meses = [mapa_meses[m] for m in meses_disponiveis]

col1, col2 = st.columns(2)
with col1:
    mes_nome = st.selectbox("📅 Selecione o mês", opcoes_meses)
    mes = [k for k, v in mapa_meses.items() if v == mes_nome][0]
with col2:
    cliente = st.selectbox("🏢 Selecione o cliente", sorted(df["cliente"].unique()))

# ---------------------------
# FILTRO + EXIBIÇÃO
# ---------------------------
df_filtrado = df[(df["mes"] == mes) & (df["cliente"] == cliente)].copy()

# Formatar percentuais (se existirem)
for col in ["perc_icms", "perc_pis", "perc_cofins"]:
    if col in df_filtrado.columns:
        df_filtrado[col] = df_filtrado[col].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else "")
    else:
        df_filtrado[col] = ""

# Selecionar colunas que devem existir
colunas_finais = {
    "codigo_barras": "Cod. de Barras",
    "descricao": "Descrição",
    "ncm": "NCM",
    "cest": "CEST",
    "valor_vendido": "Valor Vendido",
    "valor_icms": "Valor ICMS",       "perc_icms": "% ICMS",
    "valor_pis": "Valor PIS",         "perc_pis": "% PIS",
    "valor_cofins": "Valor COFINS",   "perc_cofins": "% COFINS"
}

colunas_existentes = [col for col in colunas_finais if col in df_filtrado.columns]
df_final = df_filtrado[colunas_existentes].rename(columns=colunas_finais)

st.dataframe(df_final, use_container_width=True)
