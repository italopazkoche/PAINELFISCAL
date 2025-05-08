import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
from datetime import datetime

def run_xml_saida_mes():
    st.title("🛍️ Resumo Venda por Item")

    # Configurações de autenticação e cliente BigQuery
    credenciais_path = "C:/Users/Casi/Desktop/bdxml-459201-61af2bc44fc9.json"
    project_id = "bdxml-459201"
    credentials = service_account.Credentials.from_service_account_file(credenciais_path)
    client = bigquery.Client(credentials=credentials, project=project_id)

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

    # Carrega dados
    df = carregar_nfce_saida()

    # Pivotar meses para colunas
    df_pivot = df.pivot_table(
        index=["razao_social_emitente", "uf_origem", "cnpj_emitente"],
        columns="mes",
        values="valor_total",
        fill_value=0
    ).reset_index()

    # Renomeia colunas de mês
    meses = {
        1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai",
        6: "Jun", 7: "Jul", 8: "Ago", 9: "Set", 10: "Out",
        11: "Nov", 12: "Dez"
    }
    df_pivot.rename(columns=meses, inplace=True)

    # Soma total
    colunas_presentes = [col for col in meses.values() if col in df_pivot.columns]
    df_pivot["Total"] = df_pivot[colunas_presentes].sum(axis=1)

    st.subheader("📊 Vendas por Cliente e Mês")
    st.dataframe(df_pivot, use_container_width=True)

    # Clientes sem movimentação no mês anterior
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
        st.warning(f"A coluna do mês {nome_mes_anterior} não está presente nos dados.")
