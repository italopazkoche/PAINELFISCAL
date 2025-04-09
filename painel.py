import streamlit as st
from utils import consultar, formatar_moeda
import plotly.express as px

# Função para exibir as métricas principais
def exibir_metricas():
    # === MÉTRICAS BASE ===
    total_notas = consultar("SELECT COUNT(*) AS total FROM nfce;")['total'][0]
    total_itens = consultar("SELECT COUNT(*) AS total FROM nfce_itens;")['total'][0]
    total_cnpjs = consultar("SELECT COUNT(DISTINCT cnpj_emitente) AS total FROM nfce;")['total'][0]
    total_faturado = consultar("SELECT SUM(valor_total) AS total FROM nfce;")['total'][0]

    # Cálculos derivados
    ticket_medio = total_faturado / total_notas if total_notas > 0 else 0
    itens_por_nota = total_itens / total_notas if total_notas > 0 else 0

    # === EXIBIÇÃO DAS MÉTRICAS ===
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("🧾 Notas Emitidas", f"{total_notas:,}".replace(",", "."))
    col2.metric("📦 Itens Importados", f"{total_itens:,}".replace(",", "."))
    col3.metric("🧮 Itens por Nota", f"{itens_por_nota:.2f}")
    col4.metric("🏢 CNPJs Únicos", total_cnpjs)
    col5.metric("💰 Faturamento Total", formatar_moeda(total_faturado))
    col6.metric("📈 Ticket Médio", formatar_moeda(ticket_medio))

# Função para exibir o faturamento por cliente com filtro por UF
def exibir_faturamento_cliente():
    # === FATURAMENTO POR CLIENTE COM FILTRO POR UF ===
    st.markdown("---")
    st.subheader("💵 Faturamento por Cliente")

    ufs_disponiveis = consultar("""
        SELECT DISTINCT uf_origem 
        FROM nfce 
        WHERE uf_origem IS NOT NULL AND uf_origem != ''
        ORDER BY uf_origem;
    """)["uf_origem"].tolist()

    uf_selecionada = st.selectbox("Selecione a UF para filtrar os clientes:", ["Todas"] + ufs_disponiveis)

    query_clientes = """
        SELECT 
            nf.uf_origem,
            nf.cnpj_emitente,
            MAX(nf.razao_social_emitente) AS razao_social_emitente,  -- Pegando uma razão social qualquer
            SUM(ni.valor_total) AS total_faturado,  -- Soma corretamente os valores da tabela nfce_itens
            COUNT(DISTINCT nf.id) AS total_notas,  -- Contagem das notas fiscais únicas
            COUNT(DISTINCT ni.codigo_produto) AS total_itens,  -- Contagem dos códigos de produto distintos
            SUM(ni.valor_total) / COUNT(DISTINCT nf.id) AS ticket_medio,  -- Cálculo do ticket médio
            COUNT(DISTINCT nf.id) AS quantidade_notas  -- Contagem de todas as notas emitidas
        FROM nfce nf
        JOIN nfce_itens ni ON nf.chave_acesso = ni.chave_acesso
    """
    if uf_selecionada != "Todas":
        query_clientes += f" WHERE nf.uf_origem = '{uf_selecionada}'"

    query_clientes += """
        GROUP BY nf.uf_origem, nf.cnpj_emitente  -- Agrupamos apenas pelo CNPJ
        ORDER BY total_faturado DESC;
    """

    faturamento = consultar(query_clientes)

    # Reorganizando as colunas para garantir que a razão social seja a segunda coluna
    faturamento = faturamento[["razao_social_emitente", "uf_origem", "cnpj_emitente", "total_faturado", "total_itens", "ticket_medio", "quantidade_notas"]]
    
    # Formatando as colunas
    faturamento["total_faturado"] = faturamento["total_faturado"].apply(formatar_moeda)
    faturamento["ticket_medio"] = faturamento["ticket_medio"].apply(formatar_moeda)
    
    # Exibindo a tabela
    st.dataframe(faturamento, use_container_width=True)

# Função para exibir o valor importado por estado
def exibir_valor_importado_uf():
    # === VALOR IMPORTADO POR ESTADO ===
    st.markdown("---")
    st.subheader("🌎 Valor Importado por UF de Origem")
    
    estados = consultar("""
        SELECT 
            nf.uf_origem,
            SUM(ni.valor_total) AS valor_total
        FROM nfce nf
        JOIN nfce_itens ni ON nf.chave_acesso = ni.chave_acesso
        GROUP BY nf.uf_origem
        ORDER BY valor_total DESC;
    """)
    estados["valor_total"] = estados["valor_total"].apply(formatar_moeda)
    st.dataframe(estados, use_container_width=True)

# Função para exibir os meses com notas e valor total
def exibir_periodos_com_notas():
    # === MESES COM NOTAS E VALOR TOTAL ===
    st.markdown("---")
    st.subheader("📅 Períodos com NFC-e Importadas")

    meses = consultar("""
        SELECT 
            YEAR(data_emissao) AS ano,
            MONTH(data_emissao) AS mes,
            SUM(valor_total) AS valor_total
        FROM nfce
        GROUP BY ano, mes
        ORDER BY ano DESC, mes DESC;
    """)
    meses["valor_total"] = meses["valor_total"].apply(formatar_moeda)
    st.dataframe(meses, use_container_width=True)

# Função principal que executa o painel
def runpainel():
    st.title("📊 Painel de Inteligência Fiscal - NFC-e")

    # Exibe as métricas principais
    exibir_metricas()

    # Exibe o faturamento por cliente
    exibir_faturamento_cliente()

    # Exibe o valor importado por estado
    exibir_valor_importado_uf()

    # Exibe os períodos com notas e valor total
    exibir_periodos_com_notas()

    # Rodapé
    st.markdown("---")
    st.caption("Versão Geral")
