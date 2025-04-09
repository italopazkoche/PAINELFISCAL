import streamlit as st
from utils import consultar, formatar_moeda

def runrelatorio():
    st.title("📄 Relatório Individual por CNPJ")

    # Consulta para obter os clientes e os CNPJs
    clientes = consultar("""
        SELECT DISTINCT cnpj_emitente, razao_social_emitente 
        FROM nfce 
        ORDER BY razao_social_emitente;
    """)
    clientes["label"] = clientes["razao_social_emitente"] + " (" + clientes["cnpj_emitente"] + ")"
    
    # Criando um dicionário para mapear o nome e CNPJ
    cnpj_map = dict(zip(clientes["label"], clientes["cnpj_emitente"]))
    
    cliente_escolhido = st.selectbox("Selecione o CNPJ do Cliente", clientes["label"])
    
    # Obtendo o CNPJ real a partir do nome escolhido
    cnpj_filtro = cnpj_map[cliente_escolhido]

    st.markdown("---")
    st.subheader("📌 Resumo das Notas Emitidas")

    # Organizando o resumo das notas em 3 colunas
    col1, col2, col3 = st.columns(3)

    # Consulta para resumo das notas emitidas
    resumo = consultar(f"""
        SELECT COUNT(*) AS total_notas, SUM(valor_total) AS total_faturado
        FROM nfce WHERE cnpj_emitente = '{cnpj_filtro}';
    """)
    total_notas = int(resumo["total_notas"][0])
    total_faturado = resumo["total_faturado"][0]  # Sem aplicar a formatação aqui

    # Calculando o ticket médio
    ticket_medio = total_faturado / total_notas if total_notas > 0 else 0

    with col1:
        st.metric("📈 Ticket Médio", formatar_moeda(ticket_medio))
    
    with col2:
        st.metric("📦 Total de Notas", total_notas)

    with col3:
        st.metric("💰 Valor Total Faturado", formatar_moeda(total_faturado))

    st.markdown("---")
    st.subheader("🛒 Impostos Sobre a Venda")

    # Consulta corrigida com JOIN entre nfce_itens e nfce (sem LIMIT 30)
    itens = consultar(f"""
        SELECT 
            ni.descricao,
            SUM(ni.quantidade) AS qtd, 
            SUM(ni.valor_total) AS valor,
            MIN(ni.valor_unitario) AS menor_valor_unitario,
            MAX(ni.valor_unitario) AS maior_valor_unitario,
            MAX(ni.valor_unitario) - MIN(ni.valor_unitario) AS variacao_preco,
            AVG(ni.valor_unitario) AS media_valor_unitario,
            SUM(ni.valor_icms) AS total_icms,
            SUM(ni.valor_pis) AS total_pis,
            SUM(ni.valor_cofins) AS total_cofins
        FROM nfce_itens ni
        JOIN nfce nf ON ni.chave_acesso = nf.chave_acesso
        WHERE nf.cnpj_emitente = '{cnpj_filtro}'
        GROUP BY ni.descricao
    """)

    # Garantindo que os valores numéricos sejam float
    total_icms = float(itens["total_icms"].sum())  # Garantir que seja um número
    total_pis = float(itens["total_pis"].sum())    # Garantir que seja um número
    total_cofins = float(itens["total_cofins"].sum())  # Garantir que seja um número

    # Calculando o percentual de débito de ICMS, PIS e COFINS em relação ao total faturado
    percentual_icms = (total_icms / total_faturado) * 100 if total_faturado > 0 else 0
    percentual_pis = (total_pis / total_faturado) * 100 if total_faturado > 0 else 0
    percentual_cofins = (total_cofins / total_faturado) * 100 if total_faturado > 0 else 0

    # Calculando o percentual de cada item em relação ao total faturado
    itens["percentual_produto"] = (itens["valor"] / total_faturado) * 100

    # Formatando as colunas de valores em moeda
    itens["valor"] = itens["valor"].apply(formatar_moeda)
    itens["menor_valor_unitario"] = itens["menor_valor_unitario"].apply(formatar_moeda)
    itens["maior_valor_unitario"] = itens["maior_valor_unitario"].apply(formatar_moeda)
    itens["variacao_preco"] = itens["variacao_preco"].apply(formatar_moeda)
    itens["media_valor_unitario"] = itens["media_valor_unitario"].apply(formatar_moeda)
    itens["total_icms"] = itens["total_icms"].apply(formatar_moeda)
    itens["total_pis"] = itens["total_pis"].apply(formatar_moeda)
    itens["total_cofins"] = itens["total_cofins"].apply(formatar_moeda)
    itens["percentual_produto"] = itens["percentual_produto"].apply(lambda x: f"{x:.2f}%")

    # Organizando os cartões de débito de ICMS, PIS e COFINS em 4 colunas
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("📊 Débito de ICMS", formatar_moeda(total_icms))
        st.metric("📊 % Débito de ICMS", f"{percentual_icms:.2f}%")
    
    with col2:
        st.metric("📊 Débito de PIS", formatar_moeda(total_pis))
        st.metric("📊 % Débito de PIS", f"{percentual_pis:.2f}%")
    
    with col3:
        st.metric("📊 Débito de COFINS", formatar_moeda(total_cofins))
        st.metric("📊 % Débito de COFINS", f"{percentual_cofins:.2f}%")

    st.markdown("---")
    st.subheader("📊 Detalhes dos Itens Vendidos")

    # Exibindo a tabela de itens com as colunas mais detalhadas
    st.dataframe(itens[['descricao', 'qtd', 'valor', 'menor_valor_unitario', 'maior_valor_unitario', 'variacao_preco', 'media_valor_unitario', 'total_icms', 'total_pis', 'total_cofins', 'percentual_produto']], use_container_width=True)

    st.markdown("---")
    st.caption("Relatório gerado para envio ao cliente.")
