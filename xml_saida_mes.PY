import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
from datetime import datetime
import os
import json

# ---------------------------
# CONFIGURAÇÃO
# ---------------------------
st.set_page_config(page_title="Resumo de XMLs de Saída por Mês", layout="wide")

# ---------------------------
# CREDENCIAIS (via Streamlit Secrets)
# ---------------------------
info = json.loads(os.environ["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
credentials = service_account.Credentials.from_service_account_info(info)
client = bigquery.Client(credentials=credentials, project=info["project_id"])

# ---------------------------
# CONSULTA AO BIGQUERY
# ---------------------------
@st.cache_data(ttl=600)
def carregar_nfce_saida():
    query = """
        SELECT 
            razao_social_emitente,
            uf_origem,
            cnpj_emitente,
            EXTRACT(MONTH FROM data_emissao) AS mes,
            ROUND(SUM(valor_total), 2) AS valor_total
        FROM `bdxml-459201.nfce_data.nfce`
        WHERE EXTRACT(YEAR FROM data_emissao) = 2025
        GROUP BY razao_social_emitente, uf_origem, cnpj_emitente, mes
    """
    return client.query(query).to_dataframe()

# ---------------------------
# TÍTULO
# ---------------------------
st.title("📦 Resumo de XMLs de Saída por Mês (2025)")

# ---------------------------
# CARREGAMENTO E PIVOTAMENTO
# ---------------------------
df = carregar_nfce_saida()

df_pivot = df.pivot_table(
    index=["razao_social_emitente", "uf_origem", "cnpj_emitente"],
    columns="mes",
    values="valor_total",
    fill_value=0
).reset_index()

# Renomear colunas dos meses
meses = {
    1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai",
    6: "Jun", 7: "Jul", 8: "Ago", 9: "Set", 10: "Out",
    11: "Nov", 12: "Dez"
}
df_pivot.rename(columns=meses, inplace=True)

# ---------------------------
# TOTALIZAÇÃO E EXIBIÇÃO PRINCIPAL
# ---------------------------
colunas_presentes = [col for col in meses.values() if col in df_pivot.columns]
df_pivot["Total"] = df_pivot[colunas_presentes].sum(axis=1)

st.subheader("📊 Vendas por Cliente e Mês")
st.dataframe(df_pivot, use_container_width=True)

# ---------------------------
# CLIENTES SEM XML NO MÊS ANTERIOR
# ---------------------------
hoje = datetime.today()
mes_atual = hoje.month
mes_anterior = mes_atual - 1 if mes_atual > 1 else 12
nome_mes_anterior = meses[mes_anterior]

st.markdown("---")
st.subheader(f"📭 Clientes sem XML importado no mês de {nome_mes_anterior}")

if nome_mes_anterior in df_pivot.columns:
    df_zerados = df_pivot[df_pivot[nome_mes_anterior] == 0][
        ["razao_social_emitente", "cnpj_emitente"]
    ].sort_values(by="razao_social_emitente")

    if df_zerados.empty:
        st.success(f"Todos os clientes possuem movimentação no mês de {nome_mes_anterior}. ✅")
    else:
        st.dataframe(df_zerados, use_container_width=True)
else:
    st.warning(f"A coluna do mês {nome_mes_anterior} não está presente nos dados carregados.")
