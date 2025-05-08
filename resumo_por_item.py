import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
import os
import json

def run_resumo_por_item():
    st.title("📈 Resumo de XMLs de Saída por Mês")

    # Autenticação com credenciais via Streamlit Secrets
    info = json.loads(os.environ["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
    credentials = service_account.Credentials.from_service_account_info(info)
    client = bigquery.Client(credentials=credentials, project=info["project_id"])

    @st.cache_data(ttl=600)
    def carregar_resumo_por_item():
        query = "SELECT * FROM `bdxml-459201.nfce_data.v_resumo_por_item_2025`"
        return client.query(query).to_dataframe()

    # Carregar os dados
    df = carregar_resumo_por_item()
    df["cliente"] = df["razao_social_emitente"] + " - " + df["cnpj_emitente"]

    # Mapas para exibir os meses com nomes amigáveis
    mapa_meses = {
        1: "Jan/25", 2: "Fev/25", 3: "Mar/25", 4: "Abr/25",
        5: "Mai/25", 6: "Jun/25", 7: "Jul/25", 8: "Ago/25",
        9: "Set/25", 10: "Out/25", 11: "Nov/25", 12: "Dez/25"
    }

    meses_disponiveis = sorted(df["mes"].unique())
    opcoes_meses = [mapa_meses[m] for m in meses_disponiveis]

    # Filtros interativos
    col1, col2 = st.columns(2)
    with col1:
        mes_nome = st.selectbox("📅 Selecione o mês", opcoes_meses)
        mes = [k for k, v in mapa_meses.items() if v == mes_nome][0]
    with col2:
        cliente = st.selectbox("🏢 Selecione o cliente", sorted(df["cliente"].unique()))

    # Filtragem de dados
    df_filtrado = df[(df["mes"] == mes) & (df["cliente"] == cliente)].copy()

    # Formatar colunas percentuais
    for col in ["perc_icms", "perc_pis", "perc_cofins"]:
        if col in df_filtrado.columns:
            df_filtrado[col] = df_filtrado[col].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else "")
        else:
            df_filtrado[col] = ""

    # Selecionar e renomear colunas finais
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

    # Exibir
    st.dataframe(df_final, use_container_width=True)
