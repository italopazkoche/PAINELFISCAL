import streamlit as st
from utils import consultar, formatar_moeda
import plotly.express as px

# === CONSTANTES DE TABELAS NO BIGQUERY ===
DATASET = "bdxml-459201.nfce_data"

NFCE = f"`{DATASET}.nfce`"
ITENS = f"`{DATASET}.nfce_itens`"

def runpainel():
    st.title("📊 Painel de Inteligência Fiscal - NFC-e")

    # === SELEÇÃO DE MÊS ===
    meses_disponiveis = consultar(f"""
        SELECT DISTINCT FORMAT_DATE('%Y-%m', DATE(data_emissao)) AS mes
        FROM {NFCE}
        ORDER BY mes DESC;
    """)["mes"].tolist()
    mes_selecionado = st.selectbox("📅 Selecione o mês de referência:", ["Todos"] + meses_disponiveis)

    # Filtro condicional para as consultas
    filtro_mes = ""
    if mes_selecionado != "Todos":
        filtro_mes = f"WHERE FORMAT_DATE('%Y-%m', DATE(data_emissao)) = '{mes_selecionado}'"

    # === MÉTRICAS BASE ===
    total_notas = consultar(f"SELECT COUNT(*) AS total FROM {NFCE} {filtro_mes};")['total'][0]
    total_itens = consultar(f"""
        SELECT COUNT(*) AS total
        FROM {ITENS} ni
        JOIN {NFCE} nf ON nf.chave_acesso = ni.chave_acesso
        {filtro_mes.replace('data_emissao', 'DATE(nf.data_emissao)')}
    """)['total'][0]
    total_cnpjs = consultar(f"SELECT COUNT(DISTINCT cnpj_emitente) AS total FROM {NFCE} {filtro_mes};")['total'][0]
    total_faturado = consultar(f"SELECT SUM(valor_total) AS total FROM {NFCE} {filtro_mes};")['total'][0]

    ticket_medio = total_faturado / total_notas if total_notas > 0 else 0
    itens_por_nota = total_itens / total_notas if total_notas > 0 else 0

    # Exibição das métricas
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("🧾 Notas Emitidas", f"{total_notas:,}".replace(",", "."))
    col2.metric("📦 Itens Importados", f"{total_itens:,}".replace(",", "."))
    col3.metric("🧮 Itens por Nota", f"{itens_por_nota:.2f}")
    col4.metric("🏢 CNPJs Únicos", total_cnpjs)
    col5.metric("💰 Faturamento Total", formatar_moeda(total_faturado))
    col6.metric("📈 Ticket Médio", formatar_moeda(ticket_medio))

    # === FATURAMENTO POR CLIENTE COM FILTRO POR UF ===
    st.markdown("---")
    st.subheader("💵 Faturamento por Cliente")

    if filtro_mes:
        uf_filtro = filtro_mes + " AND uf_origem IS NOT NULL AND uf_origem != ''"
    else:
        uf_filtro = "WHERE uf_origem IS NOT NULL AND uf_origem != ''"

    ufs_disponiveis = consultar(f"""
        SELECT DISTINCT uf_origem
        FROM {NFCE}
        {uf_filtro}
        ORDER BY uf_origem;
    """)["uf_origem"].tolist()
    uf_selecionada = st.selectbox("Selecione a UF para filtrar os clientes:", ["Todas"] + ufs_disponiveis)

    # Montar query com filtros combinados
    condicoes = []
    if mes_selecionado != "Todos":
        condicoes.append(f"FORMAT_DATE('%Y-%m', DATE(nf.data_emissao)) = '{mes_selecionado}'")
    if uf_selecionada != "Todas":
        condicoes.append(f"nf.uf_origem = '{uf_selecionada}'")
    where_clause = "WHERE " + " AND ".join(condicoes) if condicoes else ""

    query_clientes = f"""
        SELECT 
            nf.uf_origem,
            nf.cnpj_emitente,
            MAX(nf.razao_social_emitente) AS razao_social_emitente,
            SUM(ni.valor_total) AS total_faturado,
            COUNT(DISTINCT nf.id) AS total_notas,
            COUNT(DISTINCT ni.codigo_produto) AS total_itens,
            SUM(ni.valor_total) / COUNT(DISTINCT nf.id) AS ticket_medio,
            COUNT(DISTINCT nf.id) AS quantidade_notas
        FROM {NFCE} nf
        JOIN {ITENS} ni ON nf.chave_acesso = ni.chave_acesso
        {where_clause}
        GROUP BY nf.uf_origem, nf.cnpj_emitente
        ORDER BY total_faturado DESC;
    """
    faturamento = consultar(query_clientes)
    faturamento = faturamento[["razao_social_emitente", "uf_origem", "cnpj_emitente", "total_faturado", "total_itens", "ticket_medio", "quantidade_notas"]]
    faturamento["total_faturado"] = faturamento["total_faturado"].apply(formatar_moeda)
    faturamento["ticket_medio"] = faturamento["ticket_medio"].apply(formatar_moeda)
    st.dataframe(faturamento, use_container_width=True)

    # === VALOR IMPORTADO POR ESTADO ===
    st.markdown("---")
    st.subheader("🌎 Valor Importado por UF de Origem")

    query_ufs = f"""
        SELECT nf.uf_origem, SUM(ni.valor_total) AS valor_total
        FROM {NFCE} nf
        JOIN {ITENS} ni ON nf.chave_acesso = ni.chave_acesso
        {where_clause}
        GROUP BY nf.uf_origem
        ORDER BY valor_total DESC;
    """
    estados = consultar(query_ufs)
    estados["valor_total"] = estados["valor_total"].apply(formatar_moeda)
    st.dataframe(estados, use_container_width=True)

    # === PERÍODOS COM NOTAS ===
    st.markdown("---")
    st.subheader("📅 Períodos com NFC-e Importadas")
    query_meses = f"""
        SELECT 
            EXTRACT(YEAR FROM DATE(data_emissao)) AS ano,
            EXTRACT(MONTH FROM DATE(data_emissao)) AS mes,
            SUM(valor_total) AS valor_total
        FROM {NFCE}
        {filtro_mes}
        GROUP BY ano, mes
        ORDER BY ano DESC, mes DESC;
    """
    meses = consultar(query_meses)
    meses["valor_total"] = meses["valor_total"].apply(formatar_moeda)
    st.dataframe(meses, use_container_width=True)

    st.markdown("---")
    st.caption("Versão Geral")
