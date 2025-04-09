# Função para exibir os dados EFD ICMS no Streamlit
def exibir_dados_efd_icms():
    st.title("📑 Relatório EFD ICMS")
    
    # Carregar os dados dos arquivos EFD ICMS
    dados_efd = ler_efd_icms()
    
    if dados_efd.empty:
        st.warning("Não há dados para exibir.")
    else:
        # Permitir que o usuário selecione o CNPJ
        # Agora estamos desempacotando três valores, pois a função filtrar_blocos retorna 3 valores
        dados_c100, dados_c170, cnpjs_unicos = filtrar_blocos(dados_efd, None)
        
        cnpj_selecionado = st.selectbox("Selecione o CNPJ", cnpjs_unicos)
        
        # Filtrar os dados com base no CNPJ selecionado
        dados_c100, dados_c170 = filtrar_blocos(dados_efd, cnpj_selecionado)
        
        if dados_c100.empty:
            st.warning(f"Nenhum dado encontrado para o CNPJ {cnpj_selecionado} no Bloco C100.")
        else:
            # Exibir os dados do Bloco C100
            st.subheader("📊 Bloco C100")
            st.dataframe(dados_c100)

            # Exemplo de cálculos adicionais para o Bloco C100
            total_icms_c100 = dados_c100["Valor ICMS"].sum() if "Valor ICMS" in dados_c100.columns else 0
            st.metric("📊 Total ICMS", f"R$ {total_icms_c100:,.2f}".replace(",", "."))
            
            total_pis_c100 = dados_c100["Valor PIS"].sum() if "Valor PIS" in dados_c100.columns else 0
            st.metric("📊 Total PIS", f"R$ {total_pis_c100:,.2f}".replace(",", "."))
            
            total_cofins_c100 = dados_c100["Valor COFINS"].sum() if "Valor COFINS" in dados_c100.columns else 0
            st.metric("📊 Total COFINS", f"R$ {total_cofins_c100:,.2f}".replace(",", "."))
        
        if dados_c170.empty:
            st.warning(f"Nenhum dado encontrado para o CNPJ {cnpj_selecionado} no Bloco C170.")
        else:
            # Exibir os dados do Bloco C170
            st.subheader("📊 Bloco C170")
            st.dataframe(dados_c170)

            # Exemplo de cálculos adicionais para o Bloco C170
            total_valor_c170 = dados_c170["Valor Total"].sum() if "Valor Total" in dados_c170.columns else 0
            st.metric("📊 Total Valor C170", f"R$ {total_valor_c170:,.2f}".replace(",", "."))

# Função principal para rodar o relatório EFD ICMS
def run_efd_icms():
    exibir_dados_efd_icms()
